"""Etapa 4: Análisis espacial por zonas, densidad en el área y flujo."""

import numpy as np
from models.experimento import Experimento
from models.area_medicion import AreaMedicion
from models.linea_medicion import LineaMedicion
from models.metricas import distancia
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

class AnalisisEspacial(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Evalúa métricas por zonas longitudinales, densidad temporal y flujo de cruce."""

    @property
    def nombre(self) -> str:
        return "Análisis Espacial"

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> list[Experimento]:
        mitad = contexto.largo_area / 2.0
        area_central = AreaMedicion(
            nombre="Area Central",
            x_min=contexto.x_linea_flujo - mitad,
            x_max=contexto.x_linea_flujo + mitad,
            y_min=0.0,
            y_max=contexto.ancho_corredor,
        )
        linea_central = LineaMedicion(
            nombre=f"Linea x={contexto.x_linea_flujo}",
            x_pos=contexto.x_linea_flujo,
            y_min=0.0,
            y_max=contexto.ancho_corredor,
        )

        for exp in experimentos:
            exp.metricas_zonas = self._analizar_zonas(exp, contexto)
            exp.serie_densidad = self._serie_densidad(exp, area_central, contexto)
            exp.cruces_flujo = linea_central.detectar_cruces(exp, exp.fps)
            exp.flujo_ventanas = self._flujo_por_ventanas(exp.cruces_flujo, contexto.ventana_flujo_s)

        return experimentos

    def _definir_zonas(self, sentido: str, limites: tuple[float, ...]) -> list[tuple[str, float, float]]:
        """Zonas consecutivas en x, nombradas en el orden en que el peatón las recorre."""
        tramos = list(zip(limites, limites[1:]))   # de menor a mayor x
        if sentido == "-x":
            tramos = tramos[::-1]                  # quien camina hacia -x entra por el x mayor
        nombres = ["Zona Entrada", "Zona Central", "Zona Salida"]
        if len(tramos) != 3:
            nombres = [f"Zona {i + 1}" for i in range(len(tramos))]
        return [(n, a, b) for n, (a, b) in zip(nombres, tramos)]

    def _analizar_zonas(self, exp: Experimento, contexto: ContextoPipeline) -> list[dict]:
        """Por zona, cantidad de peatones, velocidad media y tiempo medio de cruce."""
        sentido = exp.sentido_caminata()
        resultados = []
        for nombre_z, xmin, xmax in self._definir_zonas(sentido, contexto.limites_zonas):
            vels_z, tiempos_z = [], []
            for t in exp.trayectorias:
                obs_z = [o for o in t.observaciones if xmin <= o.x <= xmax]
                if len(obs_z) >= 2:
                    dt = (obs_z[-1].frame - obs_z[0].frame) / exp.fps
                    if dt > 0:
                        dist_z = sum(
                            distancia((o1.x, o1.y), (o2.x, o2.y))
                            for o1, o2 in zip(obs_z, obs_z[1:])
                        )
                        vels_z.append(dist_z / dt)
                        tiempos_z.append(dt)


            resultados.append({
                "zona": nombre_z,
                "sentido_exp": sentido,
                "x_ini_m": xmin,
                "x_fin_m": xmax,
                "n_peatones": len(vels_z),
                "v_media_m_s": round(float(np.mean(vels_z)), 4) if vels_z else 0.0,
                "v_std_m_s": round(float(np.std(vels_z)), 4) if vels_z else 0.0,
                "t_medio_s": round(float(np.mean(tiempos_z)), 4) if tiempos_z else 0.0,
            })
        return resultados

    def _serie_densidad(self, exp: Experimento, area: AreaMedicion, contexto: ContextoPipeline) -> list[dict]:
        """Serie rho(t) y v(t) dentro del área, marcando estado estacionario y tramo."""
        vista = exp.vista_por_frame()
        if not vista:
            return []

        fps = exp.fps
        paso = contexto.paso_muestreo_frames
        f_min, f_max = min(vista), max(vista)
        ini_frac, fin_frac = contexto.fraccion_estacionario
        f_est_ini = f_min + int(ini_frac * (f_max - f_min))
        f_est_fin = f_min + int(fin_frac * (f_max - f_min))
        t_cambio = contexto.cambios_geometria_s.get(exp.nombre)  # None si no hay cambio


        serie = []
        for f in range(f_min, f_max + 1, paso):
            t_s = f / fps
            serie.append({
                "frame": f,
                "t_s": round(t_s, 2),
                "N": len(area.peatones_en_frame(f, vista)),
                "rho_1_m2": round(area.calcular_densidad(f, vista), 4),
                "v_media_area_m_s": round(area.calcular_velocidad_area(f, vista, fps, paso=paso), 4),
                "estado_estacionario": f_est_ini <= f <= f_est_fin,
                "tramo": 1 if t_cambio is None or t_s < t_cambio else 2,
            })
        return serie

    def _flujo_por_ventanas(self, cruces: list[dict], ancho_v: float) -> list[dict]:
        """Flujo J = N / Δt en ventanas consecutivas de ancho fijo."""
        if not cruces:
            return []
        t_max = max(c["t_cruce_s"] for c in cruces)
        bordes = np.arange(0.0, np.ceil(t_max) + ancho_v, ancho_v)
        ventanas = []
        for t0, t1 in zip(bordes, bordes[1:]):
            n_c = sum(1 for c in cruces if t0 <= c["t_cruce_s"] < t1)
            ventanas.append({
                "t_ini_s": round(float(t0), 1),
                "t_fin_s": round(float(t1), 1),
                "n_cruces": n_c,
                "J_ventana_1_s": round(n_c / ancho_v, 4),
            })
        return ventanas
