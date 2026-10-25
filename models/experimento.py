from dataclasses import dataclass, field
from typing import List, Dict, Any
from models.observacion import Observacion
from models.trayectoria import Trayectoria

@dataclass
class Experimento:
    """Una corrida del experimento: sus trayectorias, metadatos y resultados calculados."""


    nombre: str
    fps: float = 25.0
    trayectorias: List[Trayectoria] = field(default_factory=list)
    reporte_validacion: Dict[str, Any] = field(default_factory=dict)
    metricas_individuales: List[Dict[str, Any]] = field(default_factory=list)
    metricas_zonas: List[Dict[str, Any]] = field(default_factory=list)
    serie_densidad: List[Dict[str, Any]] = field(default_factory=list)
    cruces_flujo: List[Dict[str, Any]] = field(default_factory=list)
    flujo_ventanas: List[Dict[str, Any]] = field(default_factory=list)
    resumen: Dict[str, Any] = field(default_factory=dict)


    def vista_por_frame(self) -> Dict[int, List[Observacion]]:
        """Índice temporal {frame: [Observacion, ...]} construido desde las trayectorias válidas."""
        vista: Dict[int, List[Observacion]] = {}
        for t in self.trayectorias:
            for obs in t.observaciones:
                vista.setdefault(obs.frame, []).append(obs)
        return vista


    def sentido_caminata(self) -> str:
        """
        Determina si los peatones avanzan hacia '+x' (izq a der) o hacia '-x'
        (der a izq) según el signo de la suma de los desplazamientos netos en x.
        """
        deltas_x = [
            t.observaciones[-1].x - t.observaciones[0].x
            for t in self.trayectorias
            if len(t.observaciones) >= 2
        ]
        if not deltas_x:
            return "-x"
        return "+x" if sum(deltas_x) >= 0 else "-x"
