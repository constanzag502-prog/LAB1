"""Etapa 3: Análisis cinemático individual y detenciones."""


from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

class AnalisisIndividual(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Calcula métricas individuales por peatón y estadísticas de detención."""

    @property
    def nombre(self) -> str:
        return "Análisis Individual"

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> list[Experimento]:
        v_umbral = contexto.umbral_detencion
        dur_min = contexto.duracion_min_detencion

        for exp in experimentos:
            fps = exp.fps
            paso_suave = max(1, int(round(fps)))  # paso de ~1 s para una v_max sin el ruido del balanceo
            filas = []

            for t in exp.trayectorias:
                n_det, t_det, pct_det = t.estadisticas_detencion(
                    fps=fps, v_umbral=v_umbral, duracion_min=dur_min
                )
                filas.append({
                    "id": t.id_peaton,
                    "x0_m": round(t.observaciones[0].x, 4),
                    "y0_m": round(t.observaciones[0].y, 4),
                    "xf_m": round(t.observaciones[-1].x, 4),
                    "yf_m": round(t.observaciones[-1].y, 4),
                    "T_s": round(t.calcular_tiempo_total(fps), 4),
                    "Dr_m": round(t.calcular_distancia_total(), 4),
                    "D_m": round(t.calcular_desplazamiento(), 4),
                    "v_media_m_s": round(t.calcular_velocidad_media(fps), 4),
                    "v_max_1frame_m_s": round(t.calcular_velocidad_maxima(fps, paso=1), 4),
                    "v_max_1s_m_s": round(t.calcular_velocidad_maxima(fps, paso=paso_suave), 4),
                    "E": round(t.calcular_eficiencia(), 4),
                    "n_detenciones": n_det,
                    "t_detenido_s": round(t_det, 4),
                    "pct_detenido": round(pct_det, 2),
                })


            exp.metricas_individuales = filas

        return experimentos
