# IF3070_G09_Sepakat

Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027: optimasi penataan kendaraan pada
geladak kapal kargo menggunakan algoritma *local search*.

| Kelompok | Persoalan | Algoritma |
|---|---|---|
| G09 — Sepakat | Vehicle deck loading (2D placement + knapsack) | Hill-Climbing, Simulated Annealing, Genetic Algorithm |

---

## Deskripsi Persoalan

Diberikan sebuah geladak kapal berukuran `W × L` grid dengan kapasitas berat `C`, serta daftar kendaraan
yang masing-masing memiliki dimensi `w × l`, *shipping fee*, berat, dan ETA. Program memilih kendaraan
yang diangkut beserta posisi dan orientasinya (horizontal/vertikal) sehingga total *shipping fee*
maksimum, dengan constraint:

1. Kendaraan tidak saling bertumpuk (*no overlapping*).
2. Seluruh bagian kendaraan berada di dalam batas geladak.
3. Total berat kendaraan tidak melebihi kapasitas kapal.

Detail desain (representasi state, objective, neighbor) ada di [`docs/DESIGN.md`](docs/DESIGN.md).

---

## Fitur

- **Representasi state** koordinat eksplisit `(ship, x, y, orientasi)` per kendaraan, dipakai bersama
  oleh semua algoritma.
- **Objective dengan penalty** untuk overlap, keluar batas, dan kelebihan berat, plus
  **delta evaluation** sehingga evaluasi neighbor tidak menghitung ulang seluruh grid.
- **Neighbor move** sesuai spesifikasi: pindah koordinat (termasuk ke luar/dalam kapal), tukar dua
  kendaraan, ubah orientasi.
- **Hill-Climbing**: Steepest Ascent, Stochastic, Sideways Move, Random Restart (Bonus 2).
- **Simulated Annealing**: T0 otomatis, geometric cooling, pencatatan `e^(ΔE/T)` dan frekuensi *stuck*.
- **Genetic Algorithm**: roulette wheel selection, one-point crossover, mutation, elitism.
- **Upper bound** global optimum (DP knapsack berat + luas) untuk mengukur *gap*.
- **Bonus 1**: objective alternatif berbasis ETA. **Bonus 3**: multi-kapal.
- **Visualisasi** initial/final state dan plot hasil eksperimen, serta notebook analisis.

---

## Dependencies

- Python 3.10+
- Package di [`requirements.txt`](requirements.txt): `matplotlib` (visualisasi) dan `notebook`
  (notebook analisis). Algoritma *local search* hanya memakai standard library.

---

## Struktur Repository

```
IF3070_G09_Sepakat/
├── docs/
│   ├── DESIGN.md                   # keputusan desain (sumber bab Pembahasan)
│   ├── EXPERIMENTS.md              # protokol + tabel hasil eksperimen
│   ├── PROJECT_TRACKER.md          # jadwal, pembagian tugas, checklist
│   └── Laporan_G09_Sepakat.pdf     # laporan akhir
├── notebooks/
│   └── experiments.ipynb           # analisis + visualisasi hasil dari output/
├── output/                         # hasil run: <algo>/<run_id>.json + gambar
├── tests/                          # unit test (unittest)
├── src/
│   ├── main.py                     # CLI: jalankan satu algoritma pada satu instance
│   ├── experiments.py              # jalankan seluruh eksperimen → output/
│   ├── config.py                   # parameter default algoritma (HC, SA, GA)
│   ├── data/                       # instance persoalan (JSON)
│   ├── core/                       # model persoalan
│   │   ├── problem.py              # Vehicle, Ship, Problem + load & validasi JSON
│   │   ├── generator.py            # generator instance random (seeded)
│   │   ├── state.py                # State + occupancy grid + delta evaluation
│   │   ├── objective.py            # objective (full recompute), penalty, laporan feasibility
│   │   └── bounds.py               # upper bound + brute force instance kecil
│   ├── search/                     # algoritma local search
│   │   ├── neighbors.py            # move, swap, rotate, random & full neighborhood
│   │   ├── result.py               # format hasil run yang seragam
│   │   ├── hill_climbing.py        # 4 varian Hill-Climbing
│   │   ├── simulated_annealing.py
│   │   └── genetic_algorithm.py
│   └── visualization/
│       ├── state_view.py           # gambar geladak, kendaraan di luar, dan value
│       └── plots.py                # plot objective, e^(ΔE/T), GA max/mean, ringkasan
├── requirements.txt
└── README.md
```

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Cara Menjalankan

<!-- TODO: finalisasi setelah CLI jadi -->
```bash
# satu algoritma pada satu instance
python src/main.py --algo sa --instance src/data/main.json --seed 1

# seluruh eksperimen → output/
python src/experiments.py

# notebook analisis
jupyter notebook notebooks/experiments.ipynb

# unit test
python -m unittest discover -s tests -t .
```

---

## Pembagian Tugas

| NIM | Nama | Tugas |
|---|---|---|
| 18224061 | Riantama Putra | Setup repository, input & generator instance, core model (representasi state, objective + penalty, delta evaluation, neighbor moves, upper bound), seluruh varian Hill-Climbing, multi-kapal |
| 18224059 | Tiara Kusuma Wardhani | Simulated Annealing, Genetic Algorithm, objective alternatif (ETA) |
| 18224057 | Levina Nathania Bunardi | Visualisasi, CLI, experiment runner & plot, notebook analisis, koordinator laporan |
