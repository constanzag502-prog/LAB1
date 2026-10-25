"""Etapa 5: Comparación colectiva entre experimentos."""

import numpy as np
from models.experimento import Experimento
from models.resultado_analisis import ResultadoAnalisis
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

# Si la densidad media del último tercio de la ventana estacionaria difiere en más
# de este porcentaje de la del primer tercio, la ventana no es realmente estacionaria.
TOLERANCIA_ESTACIONARIO_PCT = 20.0

def _media(valores: list[float]) -> float:
    """Promedio que devuelve NaN en vez de fallar cuando la lista está vacía."""
    return float(np.mean(valores)) if valores else float("nan")

def _flujo(cruces: list[dict]) -> float:
    """J = N / Δt entre el primer y el último cruce."""
    if len(cruces) < 2:
        return 0.0
    dt = cruces[-1]["t_cruce_s"] - cruces[0]["t_cruce_s"]
    return len(cruces) / dt if dt > 0 else 0.0

class ComparacionExperimentos(EtapaPipeline[list[Experimento], ResultadoAnalisis]):
    """Consolida métricas globales de cada experimento y construye ResultadoAnalisis."""

    @property
    def nombre(self) -> str:
        return "Comparación de Experimentos"

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> ResultadoAnalisis:
        resumenes = [self._resumir(exp, contexto) for exp in experimentos]
        resumenes.sort(key=lambda r: r["densidad_media_1_m2"])  # de menor a mayor densidad (Fase 11)
        return ResultadoAnalisis(
            experimentos=experimentos,
            comparacion={r["experimento"]: r["densidad_media_1_m2"] for r in resumenes},
            tabla_resumen=resumenes,
        )

    def _resumir(self, exp: Experimento, contexto: ContextoPipeline) -> dict:
        ind = exp.metricas_individuales
        est = [d for d in exp.serie_densidad if d["estado_estacionario"]] or exp.serie_densidad

        rho_est = _media([d["rho_1_m2"] for d in est])
        v_area_est = _media([d["v_media_area_m_s"] for d in est if d["v_media_area_m_s"] > 0])
        j_global = _flujo(exp.cruces_flujo)
        j_hidro = rho_est * v_area_est * contexto.ancho_corredor  # J ≈ ρ·v·b (RA5)

        # Criterio objetivo de estacionariedad: primer tercio vs último tercio de la ventana
        tercio = max(1, len(est) // 3)
        rho_ini = _media([d["rho_1_m2"] for d in est[:tercio]])
        rho_fin = _media([d["rho_1_m2"] for d in est[-tercio:]])
        variacion_pct = abs(rho_fin - rho_ini) / rho_ini * 100.0 if rho_ini > 0 else float("nan")

        resumen = {
            "experimento": exp.nombre,
            "sentido": exp.sentido_caminata(),
            "n_peatones": len(ind),
            "densidad_media_1_m2": round(rho_est, 4),
            "v_media_indiv_m_s": round(_media([r["v_media_m_s"] for r in ind]), 4),
            "v_media_area_m_s": round(v_area_est, 4),
            "v_max_1s_media_m_s": round(_media([r["v_max_1s_m_s"] for r in ind]), 4),
            "flujo_J_1_s": round(j_global, 4),
            "flujo_hidrodinamico_1_s": round(j_hidro, 4),
            "diferencia_J_pct": round(abs(j_hidro - j_global) / j_global * 100.0, 1) if j_global > 0 else float("nan"),
            "distancia_media_m": round(_media([r["Dr_m"] for r in ind]), 4),
            "desplazamiento_medio_m": round(_media([r["D_m"] for r in ind]), 4),
            "tiempo_medio_s": round(_media([r["T_s"] for r in ind]), 4),
            "eficiencia_media": round(_media([r["E"] for r in ind]), 4),
            "pct_tiempo_detenido": round(_media([r["pct_detenido"] for r in ind]), 2),
            "variacion_rho_ventana_pct": round(variacion_pct, 1),
            "estacionario_confiable": bool(variacion_pct <= TOLERANCIA_ESTACIONARIO_PCT),
        }
        resumen.update(self._resumir_tramos(exp, contexto))
        exp.resumen = resumen
        return resumen


    def _resumir_tramos(self, exp: Experimento, contexto: ContextoPipeline) -> dict:
        """Para experimentos con cambio de geometría documentado, métricas antes y después."""
        t_cambio = contexto.cambios_geometria_s.get(exp.nombre)
        vacio = {
            "t_cambio_geometria_s": float("nan"),
            "rho_tramo1_1_m2": float("nan"), "v_area_tramo1_m_s": float("nan"), "J_tramo1_1_s": float("nan"),
            "rho_tramo2_1_m2": float("nan"), "v_area_tramo2_m_s": float("nan"), "J_tramo2_1_s": float("nan"),
        }
        if t_cambio is None:
            return vacio

        resultado = {"t_cambio_geometria_s": t_cambio}
        for tramo in (1, 2):
            muestras = [d for d in exp.serie_densidad if d["tramo"] == tramo and d["N"] > 0]
            cruces = [c for c in exp.cruces_flujo if (c["t_cruce_s"] < t_cambio) == (tramo == 1)]
            resultado[f"rho_tramo{tramo}_1_m2"] = round(_media([d["rho_1_m2"] for d in muestras]), 4)
            resultado[f"v_area_tramo{tramo}_m_s"] = round(
                _media([d["v_media_area_m_s"] for d in muestras if d["v_media_area_m_s"] > 0]), 4)
            resultado[f"J_tramo{tramo}_1_s"] = round(_flujo(cruces), 4)
        return resultado


