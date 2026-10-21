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
│   ├── eta_experiments.py          # run Bonus 1 (objective ETA) → output/sa/ + output/summary_eta.md
│   ├── config.py                   # parameter default algoritma (HC, SA, GA)
│   ├── data/                       # instance persoalan (JSON)
│   │   ├── main.json               # instance utama eksperimen (30 kendaraan, deck 10x20)
│   │   ├── small.json              # instance kecil untuk brute force global optimum
│   │   └── multi.json              # armada 3 kapal untuk Bonus 3 (multi-kapal)
│   ├── core/                       # model persoalan
│   │   ├── problem.py              # Vehicle, Ship, Problem + load & validasi JSON
│   │   ├── generator.py            # generator instance random (seeded)
│   │   ├── state.py                # State + occupancy grid + delta evaluation
│   │   ├── objective.py            # objective (full recompute), penalty, laporan feasibility
│   │   ├── bounds.py               # upper bound + brute force instance kecil
│   │   └── eta_objective.py        # objective urgensi ETA (Bonus 1)
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

Semua perintah dijalankan dari root repository.

### Satu algoritma pada satu instance

```bash
python src/main.py --algo hc --seed 1                      # Steepest Ascent HC pada main.json
python src/main.py --algo sa --instance multi.json --seed 2 # multi-kapal (Bonus 3)
python src/main.py --algo ga --population 50 --iterations 300 --seed 3
python src/main.py --algo random_restart --max-restart 5
python src/main.py --view output/sa/main_seed1.json        # tampilkan & gambar ulang hasil yang tersimpan
```

| Opsi | Keterangan |
|---|---|
| `--algo` | `steepest` (alias `hc`), `sideways`, `random_restart`, `stochastic` (Bonus 2), `sa`, `ga` |
| `--instance` | path file instance, atau nama file di `src/data/` (`main.json`, `small.json`, `multi.json`). Default `main.json` |
| `--seed` | seed random (default 1); eksperimen memakai seed 1, 2, 3 |
| `--max-sideways`, `--max-restart`, `--max-no-improve` | parameter Sideways Move, Random Restart, Stochastic HC |
| `--max-iterations` | batas pengaman iterasi varian HC (Random Restart: per percobaan) |
| `--iterations` | iterasi SA / generasi GA |
| `--population` | ukuran populasi GA |
| `--objective` | objective yang dioptimasi; saat ini hanya `fee` (objective ETA, Bonus 1, dijalankan lewat `src/eta_experiments.py`) |
| `--out` | folder output (default `output/`) |
| `--no-plot`, `--no-save` | simpan JSON tanpa gambar / tidak menyimpan apa pun |
| `--view JSON` | baca hasil run yang sudah disimpan tanpa menjalankan search lagi |

Parameter yang tidak diisi memakai nilai default di [`src/config.py`](src/config.py). Parameter yang tidak
berlaku untuk algoritma yang dipilih (misalnya `--population` untuk `sa`) ditolak.

Program mencetak ringkasan (objective awal dan akhir, total fee, feasibility, gap terhadap upper bound,
iterasi, durasi) dan final state dalam bentuk teks, lalu menyimpan ke `output/<algo>/`:

| File | Isi |
|---|---|
| `<run_id>.json` | hasil lengkap run (format EXPERIMENTS §2): state awal/akhir, objective, history, parameter, durasi |
| `<run_id>_initial.png`, `<run_id>_final.png` | gambar state awal dan akhir: tiap geladak, kendaraan di luar kapal, value |
| `<run_id>_plot.png` | plot objective vs iterasi (GA: maksimum dan rata-rata populasi; SA: ditambah e^(ΔE/T)) |

`run_id` = `<instance>_seed<seed>`, misalnya `main_seed1`; untuk GA `<instance>_pop<P>_iter<I>_seed<seed>`,
misalnya `main_pop50_iter300_seed2`. Run dengan instance, algoritma, parameter GA, dan seed yang sama akan
menimpa file sebelumnya. `duration_s` adalah durasi search saja, tidak termasuk waktu menyimpan file dan gambar.

### Seluruh eksperimen

```bash
python src/experiments.py --dry-run          # daftar run (21 wajib, 36 dengan bonus) tanpa menjalankan
python src/experiments.py                    # semua run -> output/<algo>/ + output/summary.md
python src/experiments.py --only sa ga_pop   # sebagian grup: hc, sa, ga_iter, ga_pop, hc_variants, eta, multi
python src/experiments.py --skip-existing    # lanjutkan bila terputus (run yang JSON-nya sudah ada dilewati)
python src/experiments.py --plots-only       # gambar ulang + ringkasan dari JSON, tanpa search
python src/experiments.py --quick --out tmp_quick   # uji coba cepat dengan small.json dan parameter kecil
```

Runner memakai fungsi yang sama dengan `src/main.py`, sehingga file hasilnya sama seperti run lewat CLI.
Konfigurasi kontrol GA (populasi 100, iterasi 1000) dipakai bersama oleh tabel EXPERIMENTS §4.6 dan §4.7 dan
hanya dijalankan sekali. Grup `eta` (Bonus 1) menjalankan SA dengan objective urgensi ETA, sama persis dengan
`src/eta_experiments.py` di bawah, jadi file hasilnya sama.
`output/summary.md` berisi tabel per bagian EXPERIMENTS §4 (§4.1–§4.10) dan info mesin, ditambah `summary_*.png`.

### Bonus 1 (objective urgensi ETA)

```bash
python src/eta_experiments.py                # SA, seed 1, 2, 3 -> output/sa/main_eta_seed*.* + output/summary_eta.md
python src/eta_experiments.py --no-plots     # tanpa gambar
```

Bobot tiap kendaraan `fee · (1 + 1/(eta + 1))` (DESIGN §8). `output/summary_eta.md` membandingkan run ETA dengan
run objective fee pada seed yang sama (`output/sa/main_seed*.json`, harus sudah ada).

Notebook `notebooks/experiments.ipynb` membaca `output/**/*.json` (tanpa menjalankan search) dan menampilkan
tabel, plot per algoritma, state awal/akhir run terbaik, serta ringkasan antar-algoritma.

### Lainnya

```bash
# buat instance baru (parameter tersimpan di "meta" file output)
python src/core/generator.py --seed 1 --vehicles 30 --width 10 --length 20 --out src/data/main.json
# armada beberapa kapal: pasangan --width/--length ke-k = geladak kapal ke-k
python src/core/generator.py --seed 1 --vehicles 40 --width 10 8 6 --length 12 10 8 --out src/data/multi.json

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
