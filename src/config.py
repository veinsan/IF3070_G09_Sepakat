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

# --- Simulated Annealing (DESIGN §7.2) -------------------------------------------------------

# T0 otomatis: sampling move acak yang memperburuk, lalu T0 dipilih supaya move dengan ΔE rata-rata
# diterima dengan peluang SA_T0_ACCEPT
SA_T0_SAMPLES = 100
SA_T0_ACCEPT = 0.8

# geometric cooling T_k = T0 * alpha^k dengan alpha = (SA_T_MIN / T0)^(1 / SA_ITERATIONS), sehingga suhu
# turun tepat dari T0 ke SA_T_MIN dalam SA_ITERATIONS iterasi (sama untuk semua seed).
# 100 000 iterasi: di main.json dan multi.json hasil rata-rata naik jelas dari 20 000 ke 100 000, sedangkan
# 200 000 hanya menambah sedikit dengan durasi 2x (~2 s -> ~4 s per run).
SA_ITERATIONS = 100_000
SA_T_MIN = 0.01

# satu kejadian "stuck" = objective terbaik tidak membaik selama SA_STUCK_WINDOW iterasi berturut-turut
SA_STUCK_WINDOW = 500
