"""Resultados de los análisis realizados sobre varios experimentos."""

from dataclasses import dataclass, field
from typing import Any
from .experimento import Experimento

#  Contenedor final: los experimentos analizados y su tabla comparativa 
@dataclass
class ResultadoAnalisis:
    """Conserva los experimentos y los resultados de su comparación."""


    experimentos: list[Experimento]
    comparacion: dict[str, float] = field(default_factory=dict)
    tabla_resumen: list[dict[str, Any]] = field(default_factory=list)
