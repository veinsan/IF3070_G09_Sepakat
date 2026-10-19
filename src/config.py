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
