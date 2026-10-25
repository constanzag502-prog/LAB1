import math
from typing import List, Dict, Any, Tuple
from models.observacion import Observacion

def id_y_frame_validos(obs: Observacion) -> bool:
    """Predicado: ID positivo y frame no negativo."""
    return obs.id_peaton > 0 and obs.frame >= 0

def coordenadas_finitas(obs: Observacion) -> bool:
    """Predicado: Coordenadas reales finitas (sin NaN ni infinitos)."""
    return math.isfinite(obs.x) and math.isfinite(obs.y) and math.isfinite(obs.z)

def dentro_del_corredor(obs: Observacion) -> bool:
    """Predicado: Límites físicos reales del pasillo experimental."""
    return (-6.0 <= obs.x <= 5.5) and (-0.5 <= obs.y <= 5.5)

def filtrar_observaciones(observaciones: List[Observacion]) -> Tuple[List[Observacion], Dict[str, Any]]:
    """
    Filtra una lista de observaciones aplicando programación funcional (filter)
    y lleva el conteo exacto de descartes por categoría.
    """
    leidos = len(observaciones)

    paso1 = list(filter(id_y_frame_validos, observaciones))
    desc_id_frame = leidos - len(paso1)

    paso2 = list(filter(coordenadas_finitas, paso1))
    desc_nan = len(paso1) - len(paso2)

    paso3 = list(filter(dentro_del_corredor, paso2))
    desc_corredor = len(paso2) - len(paso3)

    reporte = {
        "leidos": leidos,
        "aceptados": len(paso3),
        "descartados_total": leidos - len(paso3),
        "detalle_descartes": {
            "id_o_frame_invalido": desc_id_frame,
            "coordenada_nula_o_infinita": desc_nan,
            "fuera_del_corredor": desc_corredor,
        },
    }
    return paso3, reporte
