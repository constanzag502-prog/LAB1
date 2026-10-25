"""Etapa 1: Carga de archivos de experimentos."""

from pathlib import Path
from cargador import cargar_experimento
from models.experimento import Experimento
from pipeline.contexto import ContextoPipeline
from pipeline.etapa import EtapaPipeline

class CargaExperimentos(EtapaPipeline[None, list[Experimento]]):
    """Carga todos los archivos .txt desde la ruta de entrada."""

    @property
    def nombre(self) -> str:
        return "Carga de Experimentos"

    def ejecutar(self, datos: None, contexto: ContextoPipeline) -> list[Experimento]:
        ruta_in = Path(contexto.ruta_entrada)
        if ruta_in.is_file():
            archivos = [ruta_in]
        else:
            archivos = sorted(ruta_in.glob("*.txt"))

        if not archivos:
            raise FileNotFoundError(f"No se encontraron archivos .txt en '{ruta_in}'")

        experimentos: list[Experimento] = []
        for archivo in archivos:
            exp = cargar_experimento(
                ruta_archivo=archivo,
                nombre_exp=archivo.stem,
                fps_override=contexto.fps,
            )
            experimentos.append(exp)
            print(f"  [OK] {exp.nombre}: {len(exp.trayectorias)} peatones leídos (FPS={exp.fps})")

        return experimentos
