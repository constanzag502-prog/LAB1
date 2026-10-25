import math
from typing import Tuple

def distancia(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Calcula la distancia euclidiana entre dos puntos 2D."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])
