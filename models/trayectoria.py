from dataclasses import dataclass, field
from functools import reduce
from typing import List, Tuple
from models.observacion import Observacion
from models.metricas import distancia

@dataclass
class Trayectoria:
    id_peaton: int
    observaciones: List[Observacion] = field(default_factory=list)

    def __post_init__(self):
        # Ordenar cronológicamente y garantizar unicidad de frames
        ordenadas = sorted(self.observaciones, key=lambda o: o.frame)
        limpias: List[Observacion] = []
        ultimo_frame = None
        for o in ordenadas:
            if o.frame != ultimo_frame:
                limpias.append(o)
                ultimo_frame = o.frame
        self.observaciones = limpias

    def tramos(self, fps: float, paso: int = 1) -> List[Tuple[int, int, float, float]]:
        """
        Retorna lista de tuplas (frame_ini, frame_fin, dt, dist) usando map y filter.
        """
        if len(self.observaciones) <= paso or fps <= 0:
            return []
        pares = zip(self.observaciones, self.observaciones[paso:])
        mapeados = map(
            lambda par: (
                par[0].frame,
                par[1].frame,
                (par[1].frame - par[0].frame) / fps,
                distancia((par[0].x, par[0].y), (par[1].x, par[1].y)),
            ),
            pares,
        )
        return list(filter(lambda t: t[2] > 0, mapeados))

    def velocidades(self, fps: float, paso: int = 1) -> List[float]:
        """Método único para obtener velocidades por tramo usando map()."""
        return list(map(lambda t: t[3] / t[2], self.tramos(fps, paso=paso)))

    def calcular_tiempo_total(self, fps: float) -> float:
        if len(self.observaciones) < 2 or fps <= 0:
            return 0.0
        return (self.observaciones[-1].frame - self.observaciones[0].frame) / fps

    def calcular_distancia_total(self) -> float:
        if len(self.observaciones) < 2:
            return 0.0
        pares = zip(self.observaciones, self.observaciones[1:])
        distancias = map(lambda p: distancia((p[0].x, p[0].y), (p[1].x, p[1].y)), pares)
        return reduce(lambda acc, d: acc + d, distancias, 0.0)

    def calcular_desplazamiento(self) -> float:
        if len(self.observaciones) < 2:
            return 0.0
        inicio, fin = self.observaciones[0], self.observaciones[-1]
        return distancia((inicio.x, inicio.y), (fin.x, fin.y))

    def calcular_velocidad_media(self, fps: float) -> float:
        t = self.calcular_tiempo_total(fps)
        return self.calcular_distancia_total() / t if t > 0 else 0.0

    def calcular_velocidad_maxima(self, fps: float, paso: int = 1) -> float:
        vels = self.velocidades(fps, paso=paso)
        return max(vels) if vels else 0.0

    def calcular_eficiencia(self) -> float:
        d_total = self.calcular_distancia_total()
        return self.calcular_desplazamiento() / d_total if d_total > 0 else 0.0

    def tiene_saltos_imposibles(self, fps: float, v_max_permitida: float = 4.0) -> bool:
        """Detecta si algún tramo supera el umbral físico razonable (ej. 4 m/s)."""
        vels = self.velocidades(fps, paso=1)
        return any(v > v_max_permitida for v in vels)

    def limpiar_saltos(self, fps: float, v_max: float = 4.0, max_consecutivos: int = 5) -> Tuple["Trayectoria", int]:
        if len(self.observaciones) < 2 or fps <= 0:
            return self, 0

        conservadas: List[Observacion] = [self.observaciones[0]]
        eliminadas = 0
        seguidos = 0
        for obs in self.observaciones[1:]:
            ref = conservadas[-1]
            dt = (obs.frame - ref.frame) / fps
            v = distancia((ref.x, ref.y), (obs.x, obs.y)) / dt if dt > 0 else float("inf")
            if v <= v_max or seguidos >= max_consecutivos:
                conservadas.append(obs)
                seguidos = 0
            else:
                eliminadas += 1
                seguidos += 1
        return Trayectoria(id_peaton=self.id_peaton, observaciones=conservadas), eliminadas

    def es_corta(self, min_frames: int = 10, min_desp: float = 0.5) -> bool:
        """True si la trayectoria tiene muy pocas observaciones o casi no se desplaza."""
        return len(self.observaciones) < min_frames or self.calcular_desplazamiento() < min_desp

    def es_trayectoria_valida(self, fps: float, min_frames: int = 10, min_desp: float = 0.5, v_limite: float = 4.0) -> bool:
        """Valida que la trayectoria no sea demasiado corta ni tenga saltos irreales."""
        return not self.es_corta(min_frames, min_desp) and not self.tiene_saltos_imposibles(fps, v_limite)

    def detectar_detenciones(self, fps: float, v_umbral: float = 0.2, duracion_min: float = 0.5) -> List[Tuple[int, int, float]]:
        """
        Retorna episodios de detención [(frame_inicio, frame_fin, duracion_s)]
        incluyendo el caso borde al final de la trayectoria.
        """
        tramos_lista = self.tramos(fps, paso=1)
        episodios: List[Tuple[int, int, float]] = []
        en_detencion = False
        f_ini = 0
        f_fin = 0
        t_acum = 0.0

        for f1, f2, dt, dist in tramos_lista:
            v = dist / dt
            if v < v_umbral:
                if not en_detencion:
                    en_detencion = True
                    f_ini = f1
                    t_acum = 0.0
                t_acum += dt
                f_fin = f2
            else:
                if en_detencion:
                    if t_acum >= duracion_min:
                        episodios.append((f_ini, f_fin, t_acum))
                    en_detencion = False
                    t_acum = 0.0

        if en_detencion and t_acum >= duracion_min:
            episodios.append((f_ini, f_fin, t_acum))

        return episodios

    def estadisticas_detencion(self, fps: float, v_umbral: float = 0.2, duracion_min: float = 0.5) -> Tuple[int, float, float]:
        """Retorna (cantidad_detenciones, tiempo_detenido_s, pct_detenido)."""
        t_total = self.calcular_tiempo_total(fps)
        if t_total <= 0:
            return 0, 0.0, 0.0
        episodios = self.detectar_detenciones(fps, v_umbral, duracion_min)
        n_det = len(episodios)
        t_det = sum(ep[2] for ep in episodios)
        pct = (t_det / t_total) * 100.0
        return n_det, t_det, pct
