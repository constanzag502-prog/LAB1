"""Etapa 6: Exportación de tablas CSV, metadatos JSON y generación de figuras."""

import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

class ExportacionResultados(EtapaPipeline[ResultadoAnalisis, ResultadoAnalisis]):
    """Exporta todos los resultados tabulares, metadatos y gráficos en --output."""

    @property
    def nombre(self) -> str:
        return "Exportación de Resultados"

    def ejecutar(self, resultado: ResultadoAnalisis, contexto: ContextoPipeline) -> ResultadoAnalisis:
        out_dir = Path(contexto.ruta_salida)
        fig_dir = out_dir / "figuras"
        out_dir.mkdir(parents=True, exist_ok=True)
        fig_dir.mkdir(parents=True, exist_ok=True)

        validaciones_globales = {}

        # 1. Exportar CSV por cada uno de los 9 experimentos
        for exp in resultado.experimentos:
            exp_dir = out_dir / exp.nombre
            exp_dir.mkdir(parents=True, exist_ok=True)


            pd.DataFrame(exp.metricas_individuales).to_csv(exp_dir / "individuales.csv", index=False)
            pd.DataFrame(exp.metricas_zonas).to_csv(exp_dir / "zonas.csv", index=False)
            pd.DataFrame(exp.serie_densidad).to_csv(exp_dir / "densidad.csv", index=False)
            pd.DataFrame(exp.cruces_flujo).to_csv(exp_dir / "flujo.csv", index=False)
            pd.DataFrame(exp.flujo_ventanas).to_csv(exp_dir / "flujo_ventanas.csv", index=False)


            validaciones_globales[exp.nombre] = exp.reporte_validacion


            # Figura 1 por experimento: Trayectorias 2D con zonas, área y línea de flujo
            self._graficar_trayectorias(exp, contexto, fig_dir / f"trayectorias_{exp.nombre}.png")


        # 2. Exportar tabla resumen de los 9 experimentos ordenada por densidad
        df_resumen = pd.DataFrame(resultado.tabla_resumen)
        df_resumen.to_csv(out_dir / "resumen_experimentos.csv", index=False)


        # 3. Exportar configuración y conteos de validación de los 9 experimentos en JSON
        # Se escribe desde el mismo contexto que usaron las etapas: lo reportado = lo usado
        config_json = {
            "parametros_ejecucion": contexto.como_diccionario(),
            "validacion_por_experimento": validaciones_globales,
        }
        with open(out_dir / "config_y_validacion.json", "w", encoding="utf-8") as f:
            json.dump(config_json, f, indent=4, ensure_ascii=False)

        # 4. Generar las figuras comparativas globales (Figuras 2 a 7)
        self._graficar_histograma_velocidades(resultado, contexto.umbral_detencion, fig_dir / "histograma_velocidades.png")
        self._graficar_boxplots_individuales(resultado, fig_dir / "boxplot_velocidad_eficiencia.png")
        self._graficar_velocidad_por_zona(resultado, fig_dir / "velocidad_por_zona.png")
        self._graficar_series_densidad(resultado, contexto, fig_dir / "densidad_tiempo_todos.png")
        self._graficar_diagrama_fundamental(resultado, fig_dir / "diagrama_fundamental.png")
        self._graficar_diagramas_nt(resultado, contexto, fig_dir / "diagrama_nt_todos.png")

        print(f"  [OK] Tablas CSV, JSON y figuras exportadas en '{out_dir}'")
        return resultado

    def _graficar_trayectorias(self, exp, contexto: ContextoPipeline, ruta_png: Path):
        plt.figure(figsize=(10, 4))
        for t in exp.trayectorias[::2]:  # Muestreo visual limpio
            xs = [o.x for o in t.observaciones]
            ys = [o.y for o in t.observaciones]
            plt.plot(xs, ys, linewidth=0.5, alpha=0.35)

        ax = plt.gca()
        x0 = contexto.x_linea_flujo
        largo = contexto.largo_area
        rect = patches.Rectangle(
            (x0 - largo / 2.0, 0.0), largo, contexto.ancho_corredor,
            linewidth=1.5, edgecolor="green", facecolor="green", alpha=0.15, label="Área medición"
        )
        ax.add_patch(rect)
        for i, borde in enumerate(contexto.limites_zonas):
            plt.axvline(x=borde, color="gray", linestyle=":", linewidth=1.2,
                        label="Límites zonas" if i == 0 else None)
        plt.axvline(x=x0, color="red", linestyle="--", linewidth=1.8, label=f"Línea flujo (x={x0:g})")


        plt.title(f"Trayectorias y Geometría de Medición - {exp.nombre} (Sentido {exp.sentido_caminata()})")
        plt.xlabel("Posición X [m]")
        plt.ylabel("Posición Y [m]")
        plt.xlim(-6.0, 5.5)
        plt.ylim(-0.2, 5.2)
        plt.legend(loc="upper right", fontsize=8)
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(ruta_png, dpi=200)
        plt.close()

    def _graficar_histograma_velocidades(self, resultado: ResultadoAnalisis, umbral: float, ruta_png: Path):
        plt.figure(figsize=(9, 5))
        # Comparamos un experimento fluido (01) vs uno congestionado (07 o el de mayor densidad)
        exp_mayor_rho = max(resultado.experimentos, key=lambda e: e.resumen.get("densidad_media_1_m2", 0.0))
        exp_menor_rho = min(resultado.experimentos, key=lambda e: e.resumen.get("densidad_media_1_m2", 0.0))


        for exp, color in [(exp_menor_rho, "#1f77b4"), (exp_mayor_rho, "#ff7f0e")]:
            vels = []
            for t in exp.trayectorias:
                vels.extend(t.velocidades(exp.fps, paso=1))
            vels = [v for v in vels if v <= 3.5]
            plt.hist(vels, bins=50, alpha=0.55, density=True, label=f"{exp.nombre}", color=color, edgecolor="black")


        plt.axvline(x=umbral, color="red", linestyle="--", linewidth=2, label=f"Umbral detención ({umbral} m/s)")
        plt.title("Histograma de Velocidades Instantáneas y Umbral de Detención")
        plt.xlabel("Velocidad instantánea [m/s]")
        plt.ylabel("Densidad de probabilidad")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(ruta_png, dpi=250)
        plt.close()


    def _graficar_boxplots_individuales(self, resultado: ResultadoAnalisis, ruta_png: Path):
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        nombres = [e.nombre.replace("traj_UNI_CORR_500_", "Exp ") for e in resultado.experimentos]
        datos_v = [[r["v_media_m_s"] for r in e.metricas_individuales] for e in resultado.experimentos]
        datos_e = [[r["E"] for r in e.metricas_individuales] for e in resultado.experimentos]


        axes[0].boxplot(datos_v, tick_labels=nombres, patch_artist=True, boxprops=dict(facecolor="#1f77b4", alpha=0.7))
        axes[0].set_title("Velocidad Media por Peatón en los 9 Experimentos")
        axes[0].set_xlabel("Experimento")
        axes[0].set_ylabel("Velocidad media [m/s]")
        axes[0].tick_params(axis="x", rotation=45)
        axes[0].grid(True, linestyle="--", alpha=0.4)


        axes[1].boxplot(datos_e, tick_labels=nombres, patch_artist=True, boxprops=dict(facecolor="#2ca02c", alpha=0.7))
        axes[1].set_title("Eficiencia de Trayectoria (D / Dr) en los 9 Experimentos")
        axes[1].set_xlabel("Experimento")
        axes[1].set_ylabel("Eficiencia E [-]")
        axes[1].tick_params(axis="x", rotation=45)
        axes[1].grid(True, linestyle="--", alpha=0.4)


        plt.tight_layout()
        plt.savefig(ruta_png, dpi=250)
        plt.close()


    def _graficar_velocidad_por_zona(self, resultado: ResultadoAnalisis, ruta_png: Path):
        plt.figure(figsize=(12, 5))
        nombres = [e.nombre.replace("traj_UNI_CORR_500_", "Exp ") for e in resultado.experimentos]
        x = np.arange(len(nombres))
        ancho = 0.25


        zonas_labels = ["Zona Entrada", "Zona Central", "Zona Salida"]
        colores = ["#1f77b4", "#ff7f0e", "#2ca02c"]


        for idx, z_label in enumerate(zonas_labels):
            medias = []
            stds = []
            for e in resultado.experimentos:
                fila_z = next((z for z in e.metricas_zonas if z["zona"] == z_label), None)
                medias.append(fila_z["v_media_m_s"] if fila_z else 0.0)
                stds.append(fila_z["v_std_m_s"] if fila_z else 0.0)
            plt.bar(x + (idx - 1) * ancho, medias, ancho, yerr=stds, capsize=3, label=z_label, color=colores[idx], alpha=0.85)


        plt.title("Velocidad Media por Zona (con Dispersión) según Sentido de Avance")
        plt.xlabel("Experimento")
        plt.ylabel("Velocidad media [m/s]")
        plt.xticks(x, nombres)
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.4)
        plt.tight_layout()
        plt.savefig(ruta_png, dpi=250)
        plt.close()


    def _graficar_series_densidad(self, resultado: ResultadoAnalisis, contexto: ContextoPipeline, ruta_png: Path):
        fig, axes = plt.subplots(3, 3, figsize=(15, 10), sharex=False, sharey=True)
        axes_flat = axes.flatten()


        for idx, exp in enumerate(resultado.experimentos[:9]):
            ax = axes_flat[idx]
            ts = [d["t_s"] for d in exp.serie_densidad]
            rhos = [d["rho_1_m2"] for d in exp.serie_densidad]
            est_ts = [d["t_s"] for d in exp.serie_densidad if d["estado_estacionario"]]


            ax.plot(ts, rhos, color="#1f77b4", linewidth=1.2, label=r"$\rho(t)$")
            if est_ts:
                ax.axvspan(est_ts[0], est_ts[-1], color="orange", alpha=0.2, label="Ventana estacionaria")
            t_cambio = contexto.cambios_geometria_s.get(exp.nombre)
            if t_cambio is not None:
                ax.axvline(t_cambio, color="red", linestyle="--", linewidth=1.2, label="Cambio de salida")
                ax.legend(fontsize=7)
            titulo = exp.nombre.replace("traj_UNI_CORR_500_", "Exp ")
            if not exp.resumen.get("estacionario_confiable", True):
                titulo += " (no estacionario)"
            ax.set_title(titulo, fontsize=10, fontweight="bold")
            ax.set_xlabel("Tiempo [s]", fontsize=8)
            ax.set_ylabel(r"Densidad [p/m$^2$]", fontsize=8)
            ax.grid(True, linestyle="--", alpha=0.4)
            if idx == 0:
                ax.legend(fontsize=7)


        plt.suptitle(r"Evolución Temporal de la Densidad $\rho(t)$ y Ventana Estacionaria", fontsize=14, fontweight="bold")
        plt.tight_layout()
        plt.savefig(ruta_png, dpi=250)
        plt.close()


    def _graficar_diagrama_fundamental(self, resultado: ResultadoAnalisis, ruta_png: Path):
        """Punto 7: Diagrama fundamental usando pares (rho, v) por frame en el área para los 9 experimentos."""
        plt.figure(figsize=(10, 6))
        cmap = plt.get_cmap("tab10")


        for idx, exp in enumerate(resultado.experimentos):
            pares = [
                (d["rho_1_m2"], d["v_media_area_m_s"])
                for d in exp.serie_densidad
                if d["estado_estacionario"] and d["N"] > 0 and d["v_media_area_m_s"] > 0
            ]
            if pares:
                rhos, vels = zip(*pares)
                etiqueta = exp.nombre.replace("traj_UNI_CORR_500_", "Exp ")
                plt.scatter(rhos, vels, s=18, alpha=0.55, color=cmap(idx % 10), label=etiqueta)


        # Superponer los promedios estacionarios de cada experimento como marcadores grandes
        for idx, exp in enumerate(resultado.experimentos):
            r_med = exp.resumen.get("densidad_media_1_m2", 0.0)
            v_med = exp.resumen.get("v_media_area_m_s", 0.0)
            plt.scatter([r_med], [v_med], s=110, color=cmap(idx % 10), edgecolors="black", linewidth=1.5, zorder=5)


        plt.title(r"Diagrama Fundamental Peatonal: Velocidad vs Densidad en el Área ($v$ vs $\rho$)")
        plt.xlabel(r"Densidad en el área $\rho$ [peatones / m$^2$]")
        plt.ylabel(r"Velocidad instantánea en el área $v$ [m/s]")
        plt.legend(title="Experimentos", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(ruta_png, dpi=250)
        plt.close()


    def _graficar_diagramas_nt(self, resultado: ResultadoAnalisis, contexto: ContextoPipeline, ruta_png: Path):
        plt.figure(figsize=(10, 6))
        cmap = plt.get_cmap("tab10")


        for idx, exp in enumerate(resultado.experimentos):
            tiempos = [c["t_cruce_s"] for c in exp.cruces_flujo]
            if tiempos:
                n_acum = np.arange(1, len(tiempos) + 1)
                j_val = exp.resumen.get("flujo_J_1_s", 0.0)
                etiqueta = f"{exp.nombre.replace('traj_UNI_CORR_500_', 'Exp ')} (J={j_val:.2f} p/s)"
                plt.step(tiempos, n_acum, where="post", linewidth=1.8, color=cmap(idx % 10), label=etiqueta)
                t_cambio = contexto.cambios_geometria_s.get(exp.nombre)
                if t_cambio is not None:
                    plt.axvline(t_cambio, color=cmap(idx % 10), linestyle="--", linewidth=1.0)


        plt.title("Diagrama N-t (Conteo Acumulado de Cruces vs Tiempo) - 9 Experimentos")
        plt.xlabel("Tiempo [s]")
        plt.ylabel("Peatones acumulados N [personas]")
        plt.legend(loc="upper left", fontsize=8)
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(ruta_png, dpi=250)
        plt.close()
