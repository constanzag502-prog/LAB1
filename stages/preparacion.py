"""Etapa 2: Preparación y validación física de las trayectorias."""
from models.experimento import Experimento
from models.trayectoria import Trayectoria
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

class PreparacionTrayectorias(EtapaPipeline[list[Experimento], list[Experimento]]):
    """Limpia saltos imposibles punto a punto y descarta trayectorias inutilizables."""

    @property
    def nombre(self) -> str:
        return "Preparación de Trayectorias"

    def ejecutar(self, experimentos: list[Experimento], contexto: ContextoPipeline) -> list[Experimento]:
        for exp in experimentos:
            antes = len(exp.trayectorias)

            # 1. Limpieza punto a punto: se quitan solo las observaciones con saltos
            #    imposibles (error de seguimiento), sin botar al peatón completo.
            limpiezas = [t.limpiar_saltos(exp.fps, contexto.v_max_salto) for t in exp.trayectorias]
            trayectorias = [t for t, _ in limpiezas]
            obs_quitadas = sum(n for _, n in limpiezas)
            tray_corregidas = sum(1 for _, n in limpiezas if n > 0)

            # 2. Descarte de trayectorias cortas (filter con función predicado)
            no_cortas = list(filter(
                lambda t: not t.es_corta(contexto.min_frames, contexto.min_desplazamiento),
                trayectorias,
            ))
            n_cortas = len(trayectorias) - len(no_cortas)

            # 3. Descarte de las que siguen con saltos después de limpiar (casos irrecuperables)
            validas = list(filter(
                lambda t: not t.tiene_saltos_imposibles(exp.fps, contexto.v_max_salto),
                no_cortas,
            ))
            n_saltos = len(no_cortas) - len(validas)

            exp.trayectorias = validas
            exp.reporte_validacion.update({
                "observaciones_quitadas_por_salto": obs_quitadas,
                "trayectorias_corregidas_por_salto": tray_corregidas,
                "trayectorias_descartadas_cortas": n_cortas,
                "trayectorias_descartadas_saltos_irrecuperables": n_saltos,
                "trayectorias_validas": len(validas),
                "trayectorias_descartadas_total": antes - len(validas),
                "sentido_caminata": exp.sentido_caminata(),
            })

        return experimentos
