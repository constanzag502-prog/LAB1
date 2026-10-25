from dataclasses import dataclass
from typing import Dict, List
from models.observacion import Observacion
from models.metricas import distancia

@dataclass
class AreaMedicion:
    nombre: str
    x_min: float
    x_max: float
    y_min: float
    y_max: float


    def area(self) -> float:
        return max(0.0, (self.x_max - self.x_min) * (self.y_max - self.y_min))


    def contiene(self, x: float, y: float) -> bool:
        return (self.x_min <= x <= self.x_max) and (self.y_min <= y <= self.y_max)


    def peatones_en_frame(self, frame: int, vista_frames: Dict[int, List[Observacion]]) -> List[Observacion]:
        obs_frame = vista_frames.get(frame, [])
        return [o for o in obs_frame if self.contiene(o.x, o.y)]


    def calcular_densidad(self, frame: int, vista_frames: Dict[int, List[Observacion]]) -> float:
        a = self.area()
        if a <= 0:
            return 0.0
        return len(self.peatones_en_frame(frame, vista_frames)) / a


    def calcular_velocidad_area(self, frame: int, vista_frames: Dict[int, List[Observacion]], fps: float, paso: int = 5) -> float:
        """
        Calcula la velocidad media instantánea de los peatones que están dentro del área
        en el 'frame' evaluando su desplazamiento hacia 'frame + paso'.
        """
        obs_actuales = self.peatones_en_frame(frame, vista_frames)
        if not obs_actuales or fps <= 0:
            return 0.0


        obs_futuras = {o.id_peaton: o for o in vista_frames.get(frame + paso, [])}
        dt = paso / fps
        vels = []
        for o1 in obs_actuales:
            o2 = obs_futuras.get(o1.id_peaton)
            if o2 is not None:
                v = distancia((o1.x, o1.y), (o2.x, o2.y)) / dt
                if v <= 4.0:
                    vels.append(v)
        return sum(vels) / len(vels) if vels else 0.0
