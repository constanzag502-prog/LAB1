"""Punto de entrada del pipeline de análisis de trayectorias peatonales."""

import matplotlib
matplotlib.use("Agg")  # el servidor no tiene pantalla, las figuras se guardan como PNG

import argparse
from pathlib import Path
from typing import Sequence
from pipeline.contexto import ContextoPipeline
from pipeline.pipeline import Pipeline
from stages import (
    CargaExperimentos,
    PreparacionTrayectorias,
    AnalisisIndividual,
    AnalisisEspacial,
    ComparacionExperimentos,
    ExportacionResultados,
)

def crear_parser() -> argparse.ArgumentParser:
    """Crea el analizador de argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Pipeline de análisis de trayectorias peatonales (experimentos UNI_CORR_500)."
    )
    parser.add_argument(
        "--input", type=Path, default=Path("./data"),
        help="Archivo o directorio con los .txt de entrada (por defecto: ./data).",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("./results"),
        help="Directorio de salida (por defecto: ./results).",
    )
    parser.add_argument(
        "--fps", type=float, default=None,
        help="Cuadros por segundo. Si se indica, sobrescribe el '# framerate' de cada archivo.",
    )
    parser.add_argument(
        "--umbral-detencion", type=float, default=0.2,
        help="Velocidad [m/s] bajo la cual un tramo se considera detenido (por defecto: 0.2).",
    )
    parser.add_argument(
        "--duracion-detencion", type=float, default=0.5,
        help="Duración mínima [s] de un episodio de detención (por defecto: 0.5).",
    )
    parser.add_argument(
        "--v-max-salto", type=float, default=4.0,
        help="Velocidad [m/s] sobre la cual un tramo se considera error de seguimiento (por defecto: 4.0).",
    )
    parser.add_argument(
        "--largo-area", "--ancho-zona", dest="largo_area", type=float, default=2.0,
        help="Largo [m] en x del área de medición de densidad, centrada en x=0 (por defecto: 2.0). "
             "'--ancho-zona' se mantiene como alias.",
    )
    return parser

def main(argumentos: Sequence[str] | None = None) -> int:
    """Configura y ejecuta las 6 etapas del pipeline."""
    configuracion = crear_parser().parse_args(argumentos)
    configuracion.output.mkdir(parents=True, exist_ok=True)

    contexto = ContextoPipeline(
        ruta_entrada=configuracion.input,
        ruta_salida=configuracion.output,
        fps=configuracion.fps,
        umbral_detencion=configuracion.umbral_detencion,
        duracion_min_detencion=configuracion.duracion_detencion,
        v_max_salto=configuracion.v_max_salto,
        largo_area=configuracion.largo_area,
    )

    etapas = [
        CargaExperimentos(),
        PreparacionTrayectorias(),
        AnalisisIndividual(),
        AnalisisEspacial(),
        ComparacionExperimentos(),
        ExportacionResultados(),
    ]
    pipeline = Pipeline(etapas)

    print("Configuración seleccionada:")
    print(f"  Entrada: {contexto.ruta_entrada}")
    print(f"  Salida: {contexto.ruta_salida}")
    frecuencia = str(contexto.fps) if contexto.fps is not None else "leída de cabecera (# framerate)"
    print(f"  Frecuencia (fps): {frecuencia}")
    print(f"  Detención: v < {contexto.umbral_detencion} m/s durante >= {contexto.duracion_min_detencion} s")
    print(f"  Salto imposible: v > {contexto.v_max_salto} m/s")
    print(f"  Largo del área de medición: {contexto.largo_area} m")

    return 0 if pipeline.ejecutar(contexto) else 1

if __name__ == "__main__":
    raise SystemExit(main())
