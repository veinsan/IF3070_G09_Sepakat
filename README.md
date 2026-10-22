# CARGO: IF3070_G09_Sepakat

**CARGO** (*Constraint-Aware Revenue and Geometric Optimization for Vehicle Loading on Cargo Ships*) adalah program Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027. Program ini memilih kendaraan yang diangkut serta menentukan posisi dan orientasinya di geladak kapal dengan algoritma *local search*. Tujuannya memaksimalkan total *shipping fee* tanpa tumpang tindih, tanpa keluar batas geladak, dan tanpa melebihi kapasitas berat.

Algoritma yang diimplementasikan:
- Hill-Climbing: Steepest Ascent, Sideways Move, Random Restart, dan Stochastic
- Simulated Annealing
- Genetic Algorithm

Bonus yang dikerjakan: *objective* alternatif berbobot urgensi ETA, seluruh varian Hill-Climbing, dan multi-kapal.

| Folder | Isi |
|---|---|
| `src/` | *Source code* (model persoalan, algoritma, visualisasi, CLI, runner eksperimen, simulator web) |
| `dataset/` | Instance masukan: `main.json`, `small.json`, `multi.json` |
| `output/` | Hasil *run* resmi (`experiments/`) dan gambar analisis (`analysis/`) |
| `notebooks/` | Notebook analisis eksperimen |
| `docs/` | Laporan (PDF) |
| `tests/` | *Unit test* |

## Setup

Membutuhkan Python 3.11 atau lebih baru. Jalankan dari *root repository*:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Menjalankan Program

### Satu algoritma (CLI)

```bash
python src/main.py --algo steepest --seed 1
python src/main.py --algo sideways --max-sideways 100
python src/main.py --algo random_restart --max-restart 10
python src/main.py --algo stochastic --seed 2
python src/main.py --algo sa --iterations 100000
python src/main.py --algo ga --population 100 --iterations 1000
python src/main.py --algo sa --objective eta          # Bonus 1: objective ETA
python src/main.py --algo steepest --instance multi.json   # Bonus 3: multi-kapal
```

| Opsi | Keterangan |
|---|---|
| `--algo` | `steepest` (alias `hc`), `sideways`, `random_restart`, `stochastic`, `sa`, `ga` |
| `--instance` | Nama file di `dataset/` atau path JSON (default `main.json`) |
| `--seed` | Seed acak (default 1) |
| `--objective` | `fee` (default) atau `eta` |
| `--max-sideways`, `--max-restart` | Batas *sideways move* dan banyak *restart* |
| `--max-no-improve`, `--max-iterations` | Batas Stochastic dan batas iterasi Hill-Climbing |
| `--iterations`, `--population` | Iterasi SA, generasi GA, dan ukuran populasi GA |
| `--view JSON` | Tampilkan ulang hasil yang sudah tersimpan tanpa *search* |

Hasil disimpan di `output/runs/<algoritma>/`: file JSON (*state* awal dan akhir, nilai *objective*, durasi, iterasi) beserta gambar *state* awal, *state* akhir, dan plot *objective*. Nilai *default* parameter ada di `src/config.py`.

### Seluruh eksperimen

```bash
python src/experiments.py                  # 39 run (24 wajib + bonus)
python src/experiments.py --only sa ga_pop # grup tertentu
python src/experiments.py --plots-only     # gambar ulang dari JSON tanpa search
```

Hasil resmi ada di `output/experiments/`, dengan ringkasan di `output/experiments/summary.md`.

### Notebook analisis

```bash
jupyter notebook notebooks/experiments.ipynb
```

### Simulator web

```bash
python src/web_app.py
```

Buka `http://127.0.0.1:8000`. Pilih data, algoritma, *objective*, dan *seed* di panel kanan, lalu klik **Jalankan simulasi**. Proses pencarian dapat diputar ulang per *snapshot* dalam tampilan 2D atau 3D.

### Unit test

```bash
python -m unittest discover -s tests -t .
```

## Pembagian Tugas

| NIM | Nama | Tugas |
|---|---|---|
| 18224061 | Riantama Putra | Input dan generator instance, representasi *state*, *objective function* dan *delta evaluation*, *neighbor*, *upper bound*, Hill-Climbing beserta variannya, multi-kapal |
| 18224059 | Tiara Kusuma Wardhani | Simulated Annealing, Genetic Algorithm, *objective* alternatif ETA |
| 18224057 | Levina Nathania Bunardi | Visualisasi, CLI, runner eksperimen, notebook, koordinasi laporan |
