# Análisis de Dinámica Peatonal - Laboratorio 1

**Integrantes:** Constanza Guerrero, Maura Lopez, Vicente Pinto, George Jauregui

**Descripción:**
Pipeline modular automatizado en Python para el procesamiento y análisis de los 9 experimentos de trayectorias peatonales en un corredor unidireccional. El sistema ejecuta 6 etapas secuenciales (Carga, Preparación, Análisis Individual, Análisis Espacial, Comparación Colectiva y Exportación) para calcular métricas cinemáticas, episodios de detención, perfiles por zona según sentido de avance, densidad en estado estacionario, flujo con interpolación lineal y el diagrama fundamental.


---


## 1. Requisitos
- **Sistema Operativo:** Linux (Servidor remoto de la universidad, Ubuntu nativo o WSL).
- **Versión de Python:** Python 3.11 o superior (las versiones fijadas de `pandas` 3.x y `numpy` 2.x no instalan en 3.10). Verificar en el servidor con `python3 --version`.
- **Dependencias:** `pandas`, `numpy`, `matplotlib` (especificadas en `requirements.txt`).

## 2. Instalación y Configuración desde Cero (Primera vez en WSL)

Si es la primera vez que utilizas WSL en tu computador, sigue este procedimiento detallado para preparar el entorno de trabajo:

### Instalar WSL en Windows (si aún no lo tienes)
1. Abre el menú de inicio de Windows, busca **PowerShell**, haz clic derecho sobre él y selecciona **"Ejecutar como administrador"**.
2. Ejecuta el comando de instalación:
   ```powershell
   wsl --install
   
sudo apt update && sudo apt upgrade -y

sudo apt install git -y

sudo apt install python3 python3-pip python3-venv -y

### Clonar el Repositorio e Instalar Dependencias

git clone [https://github.com/constanzag502-prog/LAB1.git](https://github.com/constanzag502-prog/LAB1.git)


cd LAB1

python3 -m venv .venv

pip install -r requirements.txt

python3 main.py --input ./data --output ./results


## 3. Formato y Ubicación de los Datos
Los 9 archivos de entrada (`traj_UNI_CORR_500_01.txt` al `traj_UNI_CORR_500_09.txt`) deben ubicarse dentro de la carpeta `./data/` en la raíz del proyecto.
- **Formato esperado:** Archivos de texto plano (`.txt`) con cabeceras comentadas con `#` (incluyendo `# framerate: 25.00`) y 5 columnas separadas por espacios en blanco: `id`, `frame`, `x`, `y`, `z`, con coordenadas expresadas en metros (`[m]`).


## 4. Ejecución
El programa se ejecuta siempre desde la raíz del repositorio en modo *headless* (backend `Agg`, sin requerir pantalla gráfica):


    python3 main.py --input ./data --output ./results


Con todos los parámetros explícitos (equivale a los valores por defecto):


    python3 main.py --input ./data --output ./results --umbral-detencion 0.2 --duracion-detencion 0.5 --v-max-salto 4.0 --largo-area 2.0


Tiempo de ejecución de referencia para los 9 experimentos: menos de 1 minuto.


**Descripción de argumentos y valores por defecto:**
- `--input`: Ruta al archivo o directorio con los archivos `.txt` de entrada (por defecto: `./data`).
- `--output`: Ruta al directorio donde se exportarán las tablas CSV, el JSON y las figuras PNG (por defecto: `./results`).
- `--fps`: Frecuencia de muestreo en cuadros por segundo. Por defecto es `None` (se extrae automáticamente de `# framerate:` en la cabecera de cada archivo; si se indica por consola, sobrescribe dicho valor).
- `--umbral-detencion`: Velocidad en `[m/s]` bajo la cual un tramo se considera detenido (por defecto: `0.2`).
- `--duracion-detencion`: Duración mínima en `[s]` para contar un episodio de detención (por defecto: `0.5`).
- `--v-max-salto`: Velocidad en `[m/s]` sobre la cual un tramo se considera error de seguimiento. Esos puntos se eliminan uno a uno sin descartar al peatón (por defecto: `4.0`).
- `--largo-area`: Largo en `[m]` del área de medición de densidad, centrada en `x = 0` y con todo el ancho del corredor (por defecto: `2.0`). Se acepta también `--ancho-zona` como alias.


Los demás parámetros metodológicos (ancho del corredor, límites de las zonas, posición de la línea de flujo, ventana estacionaria, muestreo, tramos del exp 08) están definidos en un solo lugar, `pipeline/contexto.py`, y se registran completos en `results/config_y_validacion.json` en cada ejecución.


*Para consultar la ayuda en consola:* `python3 main.py --help`


## 5. Salidas Generadas
Al finalizar la ejecución, el pipeline crea automáticamente en `--output` (`./results/`) la siguiente estructura de archivos con unidades explícitas en las columnas:


- `results/<experimento>/individuales.csv`: Una fila por peatón válido con `id`, `x0_m`, `y0_m`, `xf_m`, `yf_m`, `T_s`, `Dr_m`, `D_m`, `v_media_m_s`, `v_max_1frame_m_s`, `v_max_1s_m_s`, `E`, `n_detenciones`, `t_detenido_s`, `pct_detenido`.
- `results/<experimento>/zonas.csv`: Métricas por zona según sentido de avance (`Zona Entrada`, `Zona Central`, `Zona Salida`) con `n_peatones`, `v_media_m_s`, `v_std_m_s` y `t_medio_s`.
- `results/<experimento>/densidad.csv`: Serie temporal cada 5 frames con `frame`, `t_s`, `N`, `rho_1_m2`, `v_media_area_m_s`, indicador booleano `estado_estacionario` (15% a 85% de la duración) y `tramo` (1 o 2, solo distinto de 1 en experimentos con cambio de régimen declarado).
- `results/<experimento>/flujo.csv`: Registro de cruces en `x = 0 [m]` con interpolación lineal (`id`, `frame_cruce`, `t_cruce_s`).
- `results/<experimento>/flujo_ventanas.csv`: Flujo peatonal `J_ventana_1_s` calculado en ventanas de `10 [s]`.
- `results/resumen_experimentos.csv`: Tabla comparativa de los 9 experimentos ordenada de menor a mayor densidad media. Incluye la validación hidrodinámica (`flujo_hidrodinamico_1_s` y `diferencia_J_pct`), el control de estacionariedad (`variacion_rho_ventana_pct`, `estacionario_confiable`) y, para el exp 08, densidad, velocidad y flujo antes y después del cambio de régimen (`*_tramo1_*`, `*_tramo2_*`).
- `results/config_y_validacion.json`: Todos los parámetros usados en la ejecución y, por experimento, observaciones leídas y descartadas por regla, puntos eliminados por salto, y trayectorias descartadas por cortas o por saltos irrecuperables.
- `results/figuras/*.png`: Figuras de alta resolución para el informe:
  1. `trayectorias_<experimento>.png` (para cada uno de los 9 experimentos).
  2. `histograma_velocidades.png` (justificación del umbral de detención).
  3. `boxplot_velocidad_eficiencia.png` (comparación individual de los 9 experimentos).
  4. `velocidad_por_zona.png` (barras con dispersión por zona de avance).
  5. `densidad_tiempo_todos.png` (series de tiempo marcando el estado estacionario).
  6. `diagrama_fundamental.png` (velocidad vs densidad en el área para los 9 experimentos).
  7. `diagrama_nt_todos.png` (curvas escalonadas N-t de los 9 experimentos).


## 6. Exploración (opcional)
`exploracion.ipynb` contiene la exploración inicial, el autochequeo de los cálculos y la prueba del caso borde de detenciones. Se ejecuta desde la raíz del repositorio y guarda todo en `results/exploracion/`. No es necesario para correr el pipeline.


## 7. Estructura del Repositorio


    LAB1/
    ├── data/                       # Archivos .txt de entrada de los 9 experimentos
    ├── models/                     # Entidades de datos y geometría del dominio
    │   ├── __init__.py             # Exportación de modelos
    │   ├── observacion.py          # Dataclass inmutable (frozen=True) de cada registro (frame, x, y, z)
    │   ├── trayectoria.py          # Trayectoria individual, velocidades con map/reduce, limpieza de saltos y detenciones
    │   ├── experimento.py          # Contenedor del experimento, sentido de avance y vista por frame
    │   ├── area_medicion.py        # Polígono rectangular para cálculo de densidad y velocidad espacial
    │   ├── linea_medicion.py       # Línea transversal para detección de cruces e interpolación de flujo
    │   ├── metricas.py             # Funciones matemáticas puras (distancia euclidiana)
    │   └── resultado_analisis.py   # Contenedor global de resultados de los 9 experimentos
    ├── pipeline/                   # Motor de ejecución secuencial
    │   ├── __init__.py             # Inicializador del paquete pipeline
    │   ├── contexto.py             # TODOS los parámetros de ejecución y metodológicos (ContextoPipeline)
    │   ├── etapa.py                # Clase base abstracta (EtapaPipeline)
    │   └── pipeline.py             # Orquestador de las etapas del pipeline
    ├── stages/                     # Etapas modulares de procesamiento
    │   ├── __init__.py             # Exportación de las 6 etapas
    │   ├── carga.py                # Etapa 1: Carga de los 9 archivos .txt
    │   ├── preparacion.py          # Etapa 2: Limpieza de saltos punto a punto y descarte de trayectorias cortas
    │   ├── individual.py           # Etapa 3: Cálculo de indicadores cinemáticos y detenciones
    │   ├── espacial.py             # Etapa 4: Zonas, serie de densidad y cruces de flujo
    │   ├── colectivo.py            # Etapa 5: Resumen comparativo de los 9 experimentos
    │   └── exportacion.py          # Etapa 6: Escritura de CSV, JSON y generación de figuras PNG
    ├── results/                    # Carpeta de salida generada automáticamente por main.py
    ├── cargador.py                 # Lector de cabeceras (# framerate) e ingesta con Pandas
    ├── validacion.py               # Predicados de validación espacial con filter()
    ├── main.py                     # Punto de entrada CLI con argparse y backend Agg
    ├── exploracion.ipynb           # Cuaderno de exploración y pruebas a mano (guarda en results/exploracion/, no pisa el pipeline)
    ├── decisiones.md               # Bitácora de justificación metodológica y de diseño
    ├── CAMBIOS.md                  # Registro de cambios de la versión revisada
    ├── requirements.txt            # Lista de librerías requeridas para el entorno virtual
    ├── .gitignore                  # Exclusión de .venv/, __pycache__/ y archivos temporales
    └── README.md                   # Documentación principal del proyecto
