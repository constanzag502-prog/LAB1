from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class LineaMedicion:
    nombre: str
    x_pos: float
    y_min: float
    y_max: float


    def detectar_cruces(self, experimento, fps: float) -> List[Dict[str, float]]:
        """
        Retorna lista ordenada por tiempo de diccionarios:
        {"id": id_peaton, "frame_cruce": frame_interp, "t_cruce_s": tiempo_s}
        Contando solo el primer cruce en el sentido de avance del experimento.
        """
        sentido = experimento.sentido_caminata()
        cruces = []


        for t in experimento.trayectorias:
            for o1, o2 in zip(t.observaciones, t.observaciones[1:]):
                if not (self.y_min <= o2.y <= self.y_max):
                    continue
                # Condición de cruce: cambio de signo respecto a x_pos
                if (o1.x - self.x_pos) * (o2.x - self.x_pos) <= 0:
                    dx = o2.x - o1.x
                    # Verificar que cruce en el sentido principal de avance
                    if sentido == "+x" and dx < 0:
                        continue
                    if sentido == "-x" and dx > 0:
                        continue


                    fraccion = (self.x_pos - o1.x) / dx if dx != 0 else 0.0
                    frame_cruce = o1.frame + fraccion * (o2.frame - o1.frame)
                    t_cruce = frame_cruce / fps if fps > 0 else 0.0
                    cruces.append({
                        "id": t.id_peaton,
                        "frame_cruce": round(frame_cruce, 3),
                        "t_cruce_s": round(t_cruce, 4),
                    })
                    break  # Solo el primer cruce por peatón


        cruces.sort(key=lambda c: c["t_cruce_s"])
        return cruces


    def obtener_tiempos_cruce(self, experimento, fps: float) -> List[float]:
        """Solo los instantes de cruce [s], ordenados (atajo usado en el notebook)."""
        return [c["t_cruce_s"] for c in self.detectar_cruces(experimento, fps)]
