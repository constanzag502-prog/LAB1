"""Configuración de una ejecución del pipeline."""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

@dataclass
class ContextoPipeline:
    ruta_entrada: Path
    ruta_salida: Path
    fps: float | None = None  # None = se lee de "# framerate" en cada archivo

    #Detenciones
    umbral_detencion: float = 0.2      # m/s velocidad bajo la cual se considera detenido
    duracion_min_detencion: float = 0.5  # s duración mínima de un episodio

    #Validación de trayectorias
    v_max_salto: float = 4.0           # [m/s] tramo más rápido que esto = error de seguimiento
    min_frames: int = 10               # trayectorias con menos observaciones se descartan
    min_desplazamiento: float = 0.5    # [m] desplazamiento neto mínimo

    #Geometría de medición
    ancho_corredor: float = 5.0        # [m] ancho b del pasillo (UNI_CORR_500)
    largo_area: float = 2.0            # [m] largo en x del área de medición de densidad
    x_linea_flujo: float = 0.0         # [m] posición de la línea transversal de flujo
    limites_zonas: tuple[float, ...] = (-4.5, -1.5, 1.5, 4.5)  # [m] bordes de las 3 zonas en x

    #Series temporales
    paso_muestreo_frames: int = 5      # cada cuántos frames se evalúa rho(t) y v(t)
    fraccion_estacionario: tuple[float, float] = (0.15, 0.85)  # ventana estacionaria
    ventana_flujo_s: float = 10.0      # [s] ancho de las ventanas de flujo


    #Cambios de régimen durante la corrida---
    # Tiempo [s] en que se separa la corrida en dos tramos.
    # Exp 08: la página corridor5 de Jülich documenta un cambio del ancho de salida
    # "alrededor del minuto 1:30", y en los datos el diagrama N-t muestra una meseta
    # sin cruces desde ~90 s. Las dos tablas de esa página no coinciden en los anchos
    # del 08, por eso el informe debe verificar el detalle en el JSON de metadatos.
    # Exp 09: los tiempos documentados (2:40 y 4:15) quedan fuera de los ~80 s de la
    # grabación central, así que no se declara tramo y se reporta como no estacionario.
    cambios_geometria_s: dict[str, float] = field(
        default_factory=lambda: {"traj_UNI_CORR_500_08": 90.0}
    )

    def como_diccionario(self) -> dict[str, Any]:
        """Versión serializable a JSON de toda la configuración."""
        datos = asdict(self)
        datos["ruta_entrada"] = str(self.ruta_entrada)
        datos["ruta_salida"] = str(self.ruta_salida)
        datos["limites_zonas"] = list(self.limites_zonas)
        datos["fraccion_estacionario"] = list(self.fraccion_estacionario)
        return datos
