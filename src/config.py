"""Parameter default bersama untuk CLI, runner eksperimen, dan algoritma.

Parameter khusus tiap algoritma (HC, SA, GA) ditambahkan oleh pemilik algoritmanya di bagian masing-masing,
supaya semua nilai default ada di satu tempat dan sama persis dengan yang ditulis di EXPERIMENTS.md.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "src" / "data"
OUTPUT_DIR = ROOT / "output"

# instance utama seluruh eksperimen (EXPERIMENTS §1)
DEFAULT_INSTANCE = DATA_DIR / "main.json"

# run 1/2/3 memakai seed 1, 2, 3 untuk semua algoritma (EXPERIMENTS §1)
SEEDS = (1, 2, 3)

# initial state acak: peluang tiap kendaraan langsung ditempatkan di dalam kapal (DESIGN §3)
INITIAL_P_INSIDE = 0.5

# --- Hill-Climbing (DESIGN §7.1) ---------------------------------------------------------------
# Steepest Ascent berhenti sendiri di local optimum. Batas ini hanya pengaman agar run tidak pernah
# berjalan tanpa akhir; bila tercapai, `extra["stop_reason"]` bernilai "max_iterations".
HC_MAX_ITERATIONS = 10_000

# Sideways Move: total sideways move maksimum sepanjang run (spesifikasi, DESIGN §7.1)
HC_MAX_SIDEWAYS = 100

# Random Restart: banyak restart setelah percobaan pertama (total percobaan = HC_MAX_RESTART + 1)
HC_MAX_RESTART = 10

# Stochastic: berhenti setelah sekian neighbor acak berturut-turut tidak lebih baik
HC_MAX_NO_IMPROVE = 20_000
HC_STOCHASTIC_MAX_ITERATIONS = 200_000

# --- Multi-kapal (Bonus 3, DESIGN §8) -----------------------------------------------------------
# armada 3 kapal dengan geladak 10x12, 8x10, 6x8 dan 40 kendaraan
MULTI_INSTANCE = DATA_DIR / "multi.json"

# --- Genetic Algorithm (DESIGN §7.3) ----------------------------------------------------------
# Eksperimen hanya memvariasikan populasi dan iterasi (generasi). Parameter lain tetap di semua run.
# kontrol: populasi 100 dan 1000 generasi (~1.2 s per run di main.json). Best masih membaik sampai akhir di
# 300 generasi, sedangkan 3000 generasi hanya menambah sedikit dengan durasi 3x.
GA_POPULATION = 100
GA_ITERATIONS = 1000

# variasi eksperimen (EXPERIMENTS §4.6–§4.7): satu parameter divariasikan, yang lain = nilai kontrol di atas
GA_POPULATION_VARIANTS = (50, 100, 200)
GA_ITERATION_VARIANTS = (300, 1000, 3000)

GA_P_CROSSOVER = 0.8
GA_P_MUTATION = 0.2

# banyak individu terbaik yang dibawa langsung ke generasi berikutnya (heuristik tambahan)
GA_ELITISM = 2

# windowing fitness roulette: fit_i = f_i - min_j f_j + GA_EPSILON, supaya semua peluang > 0
GA_EPSILON = 1.0
