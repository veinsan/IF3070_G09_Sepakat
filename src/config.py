"""Parameter default bersama untuk CLI, runner eksperimen, dan algoritma.

Semua nilai default ada di satu tempat dan ikut disimpan di setiap hasil JSON (`params`).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "dataset"
OUTPUT_DIR = ROOT / "output"
RUNS_DIR = OUTPUT_DIR / "runs"
EXPERIMENTS_DIR = OUTPUT_DIR / "experiments"

DEFAULT_INSTANCE = DATA_DIR / "main.json"

SEEDS = (1, 2, 3)

INITIAL_P_INSIDE = 0.5

HC_MAX_ITERATIONS = 10_000

HC_MAX_SIDEWAYS = 100

HC_MAX_RESTART = 10

HC_MAX_NO_IMPROVE = 20_000
HC_STOCHASTIC_MAX_ITERATIONS = 200_000

MULTI_INSTANCE = DATA_DIR / "multi.json"


SA_T0_SAMPLES = 100
SA_T0_ACCEPT = 0.8

SA_ITERATIONS = 100_000
SA_T_MIN = 0.01

SA_STUCK_WINDOW = 500

GA_POPULATION = 100
GA_ITERATIONS = 1000

GA_POPULATION_VARIANTS = (50, 100, 200)
GA_ITERATION_VARIANTS = (300, 1000, 3000)

GA_P_CROSSOVER = 0.8
GA_P_MUTATION = 0.2

GA_ELITISM = 2

GA_EPSILON = 1.0
