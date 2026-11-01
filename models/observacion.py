from dataclasses import dataclass


@dataclass(frozen=True)
#  Observación inmutable: posición (x, y, z) de un peatón en un frame 
class Observacion:
    """Representa una observación espaciotemporal inmutable de un peatón."""
    id_peaton: int
    frame: int
    x: float
    y: float
    z: float = 0.0
