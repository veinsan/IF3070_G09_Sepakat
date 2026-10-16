# IF3070_G09_Sepakat

Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027: optimasi penataan kendaraan pada
geladak kapal kargo menggunakan algoritma *local search* (Hill-Climbing, Simulated Annealing,
Genetic Algorithm).

## Struktur

```
src/       source code (Python)
src/data/  instance permasalahan (JSON)
output/    hasil run algoritma (JSON + gambar)
docs/      laporan (PDF) + dokumen kerja (DESIGN, EXPERIMENTS, PROJECT_TRACKER)
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run

<!-- TODO: finalisasi setelah CLI jadi -->
```bash
python src/main.py --algo sa --instance src/data/main.json --seed 1
python src/experiments.py   # menjalankan seluruh eksperimen → output/
```

## Pembagian Tugas

| NIM | Nama | Tugas |
|---|---|---|
| 18224061 | Riantama Putra | Core model (representasi state, objective + penalty, delta evaluation, neighbor moves, upper bound), seluruh varian Hill-Climbing, multi-kapal |
| 18224059 | Tiara Kusuma Wardhani | Simulated Annealing, Genetic Algorithm, objective alternatif (ETA) |
| 18224057 | Levina Nathania Bunardi | Input & generator instance, visualisasi, CLI, experiment runner & plot, koordinator laporan |
