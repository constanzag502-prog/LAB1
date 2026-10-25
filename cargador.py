import re
from pathlib import Path
import pandas as pd
from models.observacion import Observacion
from models.trayectoria import Trayectoria
from models.experimento import Experimento
from validacion import filtrar_observaciones

FPS_POR_DEFECTO = 25.0

def leer_fps_cabecera(ruta_archivo: str | Path) -> float | None:
    """Extrae el valor de '# framerate:' del encabezado del .txt, o None si no viene."""
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            for _ in range(30):
                linea = f.readline()
                if not linea:
                    break
                if linea.startswith("#"):
                    m = re.search(r"framerate\s*:\s*([0-9.]+)", linea, re.IGNORECASE)
                    if m:
                        return float(m.group(1))
                elif linea.strip():
                    break  # terminó la cabecera
    except OSError:
        pass
    return None

def cargar_experimento(
    ruta_archivo: str | Path,
    nombre_exp: str | None = None,
    fps_override: float | None = None,
) -> Experimento:
    """Lee un archivo de trayectorias, valida cada observación y arma el Experimento."""
    ruta = Path(ruta_archivo)
    if nombre_exp is None:
        nombre_exp = ruta.stem


    fps_cabecera = leer_fps_cabecera(ruta)
    if fps_override is not None:
        fps_final = fps_override
    elif fps_cabecera is not None:
        fps_final = fps_cabecera
    else:
        fps_final = FPS_POR_DEFECTO
        print(f"  [AVISO] {ruta.name} no trae '# framerate'. Se usa {FPS_POR_DEFECTO} fps. "
              f"Use --fps para indicarlo explícitamente.")


    columnas = ["id", "frame", "x", "y", "z"]
    df = pd.read_csv(
        ruta,
        sep=r"\s+",
        comment="#",
        header=None,
        names=columnas,
        encoding="utf-8",
    )

    filas_iniciales = len(df)
    df = df.drop_duplicates(subset=["id", "frame"], keep="first")
    duplicados_eliminados = filas_iniciales - len(df)

    experimento = Experimento(nombre=nombre_exp, fps=fps_final)

    reporte = {
        "archivo": ruta.name,
        "fps_cabecera": fps_cabecera,
        "fps_utilizado": fps_final,
        "observaciones_leidas": int(filas_iniciales),
        "observaciones_aceptadas": 0,
        "detalle_descartes_observaciones": {
            "duplicados_espaciotemporales": int(duplicados_eliminados),
            "id_o_frame_invalido": 0,
            "coordenada_nula_o_infinita": 0,
            "fuera_del_corredor": 0,
        },
    }

    for pid, grupo in df.groupby("id"):
        obs_crudas = [
            Observacion(
                id_peaton=int(fila.id),
                frame=int(fila.frame),
                x=float(fila.x),
                y=float(fila.y),
                z=float(fila.z),
            )
            for fila in grupo.itertuples(index=False)
        ]

        obs_validas, reporte_ind = filtrar_observaciones(obs_crudas)

        reporte["observaciones_aceptadas"] += reporte_ind["aceptados"]
        for regla, cant in reporte_ind["detalle_descartes"].items():
            reporte["detalle_descartes_observaciones"][regla] += cant

        if obs_validas:
            experimento.trayectorias.append(
                Trayectoria(id_peaton=int(pid), observaciones=obs_validas)
            )

    reporte["trayectorias_leidas"] = len(experimento.trayectorias)
    experimento.reporte_validacion = reporte
    return experimento
