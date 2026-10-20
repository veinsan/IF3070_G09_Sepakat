# Experiments Log

Semua run **harus reproducible**: instance tetap, seed tercatat, output mentah disimpan di `output/`.

## 1. Protokol

- **Instance utama:** `src/data/main.json` (n kendaraan = 30, deck = 10×20, C = 131, generator seed 1; lihat DESIGN §2).
- **Instance Bonus 3:** `src/data/multi.json` (40 kendaraan, 3 kapal: 10×12 / 8×10 / 6×8, C = 80 / 54 / 32, UB = 1318).
  Semua eksperimen wajib memakai instance ini supaya antar-algoritma bisa dibandingkan.
- **Upper bound (UB):** 1035 (lihat DESIGN §6). `gap = (UB − f) / UB`.
- **Seeds:** run 1/2/3 = seed `1`, `2`, `3` untuk semua algoritma.
- **Durasi:** wall-clock dengan `time.perf_counter()`, hanya bagian search (tidak termasuk plotting / IO).
- **Mesin:** (CPU / RAM / versi Python) __ . Semua run di satu mesin yang sama.
- Selain iterasi, catat juga **jumlah evaluasi objective**. Perbandingan antar-algoritma lebih
  adil kalau pakai jumlah evaluasi, karena satu "iterasi" Steepest HC ≠ satu iterasi SA.

## 2. Format Output per Run ✅ (`search/result.py`)

Setiap algoritma mengembalikan `RunResult`; `RunResult.to_dict()` disimpan sebagai
`output/<algo>/<run_id>.json`, contoh `output/ga/pop50_iter300_seed2.json`. `RunResult.from_dict(problem, data)`
membacanya kembali. Penamaan file dan penulisan ke disk ada di runner (`experiments.py`).

```json
{
  "algorithm": "ga", "instance": "main", "seed": 2,
  "params": { "population": 50, "iterations": 300, "p_c": 0.8, "p_m": 0.1, "elitism": 2 },
  "initial_state": {
    "vehicles": [ { "id": "V01", "ship": "Deck-1", "x": 3, "y": 0, "orientation": "H" },
                  { "id": "V02", "ship": null } ],
    "decks": [ { "id": "Deck-1", "grid": [ ["", "V01", "V01+V07", "..."], ["..."] ] } ]
  },
  "final_state": { "vehicles": ["..."], "decks": ["..."] },
  "initial_objective": -4210, "final_objective": 958, "total_fee": 958, "is_feasible": true,
  "violations": { "overlap_cells": 0, "out_of_bound_cells": 0, "weight_units": 0 },
  "used_weight": [130], "capacity": [131], "used_area_pct": 91.5, "loaded": 17,
  "upper_bound": 1035, "gap_ub": 0.0744,
  "duration_s": 3.21, "iterations": 300, "evaluations": 15000,
  "history": { "objective": [], "mean": [] },
  "extra": {}
}
```

| Field | Isi |
|---|---|
| `initial_state`, `final_state` | Pemetaan semua kendaraan (di dalam: kapal + anchor + orientasi, di luar: `ship = null`) dan pemetaan sel tiap geladak (`decks[].grid[y][x]`: `""` kosong, `"A+B"` overlap). Ini memenuhi "pemetaan semua paket dan semua koordinat" di spek |
| `final_objective`, `total_fee`, `is_feasible`, `violations` | Value state akhir dan rinciannya (DESIGN §4) |
| `used_weight`, `capacity`, `used_area_pct`, `loaded` | Utilisasi per kapal / total |
| `upper_bound`, `gap_ub` | UB instance dan `(UB − f) / UB` (DESIGN §6) |
| `duration_s` | Wall-clock search saja (`time.perf_counter()`), tanpa IO/plot |
| `iterations` | Iterasi sampai berhenti (GA: generasi; RR HC: total semua restart) |
| `evaluations` | Satu pemanggilan `State.delta()` atau satu state/individu baru yang dinilai |
| `history.objective` | Objective per iterasi, indeks 0 = state awal (GA: maksimum populasi) |
| `history.mean` | GA: rata-rata objective populasi per generasi |
| `history.prob` | SA: pasangan `[iterasi, e^(ΔE/T)]`, hanya iterasi dengan ΔE < 0 (DESIGN §7.2) |
| `params` | Parameter algoritma, termasuk `max_sideways`, `max_restart`, populasi, iterasi |
| `extra` | Data khusus: `restarts`, `iters_per_restart` (RR HC), `sideways_moves` (Sideways), `stuck_count` (SA) |

Plot dan visualisasi state dibuat **dari file JSON ini**, bukan dari run ulang. Gambar disimpan dengan
nama yang sama: `output/<algo>/<run_id>_{initial,final,plot}.png`.

## 3. Jumlah Run

| Eksperimen | Konfigurasi | Run | Wajib? |
|---|---|---|---|
| Hill-Climbing (varian utama: Steepest Ascent) | 1 | 3 | ✅ |
| Simulated Annealing | 1 | 3 | ✅ |
| GA: kontrol populasi, variasi iterasi | 3 | 9 | ✅ |
| GA: kontrol iterasi, variasi populasi | 3 | 9 | ✅ |
| HC varian lain (Bonus 2) | 3 | 9 | Bonus |
| Objective alternatif (Bonus 1) | ≥1 | 3 | Bonus |
| Multi-kapal (Bonus 3) | ≥1 | 3 | Bonus |

Total wajib: **24 run**. Dengan bonus: **39 run** (dijalankan Rab 21 pagi, lihat PROJECT_TRACKER §Jadwal).

---

## 4. Hasil

### 4.1 Hill-Climbing — Steepest Ascent

Params: `max_iterations = 10000` (hanya pengaman, tidak pernah tercapai), tie-break acak, `initial_p_inside = 0.5`

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | Evals | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |
| **mean ± std** | | | | | | | | | |

### 4.2 Hill-Climbing — Stochastic (Bonus 2)

Params: `max_iterations = 200000`, `max_no_improve = 20000`

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | Evals | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

### 4.3 Hill-Climbing — Sideways Move

Params: `max_sideways = 100` (total, DESIGN §7.1), `max_iterations = 10000` (pengaman)

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | #Sideways | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

### 4.4 Hill-Climbing — Random Restart

Params: `max_restart = 10` (total 11 percobaan Steepest Ascent)

| Run | Seed | Obj akhir | Fee | Feasible | Gap UB | #Restart | Iterasi per restart | Durasi (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | |
| 2 | 2 | | | | | | | |
| 3 | 3 | | | | | | | |

### 4.5 Simulated Annealing

Params: `T0` otomatis (100 sampel, move dengan ΔE rata-rata diterima dengan peluang 0.8), `N = 100000` iterasi
(tepat), `T_min = 0.01`, `α = (T_min / T0)^(1/N)` (≈ 0.99986, dihitung per run), stuck window `K = 500`,
`initial_p_inside = 0.5`. `final_state` = state terbaik selama pencarian (DESIGN §7.2).

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | #Stuck | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

Plot per run: objective vs iterasi, dan `e^(ΔE/T)` vs iterasi.

### 4.6 GA — Kontrol Populasi (pop = 100), Variasi Iterasi

Fixed (semua run GA): `p_c = 0.8` (one-point), `p_m = 0.2` (satu random move per anak), elitism `= 2`,
selection = **roulette wheel** dengan windowing `fit = f − min f + 1`, `initial_p_inside = 0.5`.
`initial_state` = individu terbaik populasi awal, `final_state` = individu terbaik selama pencarian (DESIGN §7.3).

| Iterasi | Run | Seed | Obj akhir (best) | Fee | Feasible | Gap UB | Durasi (s) |
|---|---|---|---|---|---|---|---|
| 300 (rendah) | 1–3 | 1,2,3 | | | | | |
| 1000 (sedang) | 1–3 | 1,2,3 | | | | | |
| 3000 (tinggi) | 1–3 | 1,2,3 | | | | | |

### 4.7 GA — Kontrol Iterasi (iter = 1000), Variasi Populasi

| Populasi | Run | Seed | Obj akhir (best) | Fee | Feasible | Gap UB | Durasi (s) |
|---|---|---|---|---|---|---|---|
| 50 (kecil) | 1–3 | 1,2,3 | | | | | |
| 100 (sedang) | 1–3 | 1,2,3 | | | | | |
| 200 (besar) | 1–3 | 1,2,3 | | | | | |

Nilai variasi ada di `config.GA_POPULATION_VARIANTS` dan `config.GA_ITERATION_VARIANTS`. Konfigurasi kontrol
(pop 100, iter 1000) muncul di kedua tabel (PROJECT_TRACKER Q&A #8).
Plot per run: **max** dan **mean** objective populasi vs generasi.

### 4.8 Bonus 3 — Multi-kapal (`multi.json`)

Algoritma: Steepest Ascent, seed 1/2/3 (SA dan GA bisa dijalankan pada instance yang sama tanpa perubahan kode).

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Berat per kapal | Kendaraan per kapal | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

### 4.9 Ringkasan Antar-Algoritma

| Algoritma | Best | Mean ± std | Gap UB (mean) | Durasi mean (s) | Evals mean |
|---|---|---|---|---|---|
| Steepest HC | | | | | |
| SA | | | | | |
| GA (config terbaik) | | | | | |

Plot ringkasan yang disarankan: box plot objective akhir per algoritma, dan overlay kurva konvergensi (x = jumlah evaluasi).

---

## 5. Checklist Analisis (untuk bab Pembahasan)

- [ ] Seberapa dekat tiap algoritma ke global optimum (pakai gap terhadap UB), dan kenapa
- [ ] Perbandingan kualitas hasil antar-algoritma
- [ ] Perbandingan durasi (per run dan per evaluasi)
- [ ] Konsistensi hasil (std / range dari 3 run)
- [ ] Pengaruh jumlah iterasi dan populasi pada GA
- [ ] Tambahan: efek penalty (apakah hasil akhir selalu feasible?), utilisasi luas & berat, efek elitism
- [ ] Tambahan: SA, hubungan frekuensi stuck dengan schedule suhu
- [ ] Tambahan: Random Restart vs Steepest, apakah restart benar-benar membantu?

## 6. Catatan / Anomali

<!-- Tulis di sini kalau ada run aneh, bug yang ketemu saat eksperimen, atau run yang harus diulang (beserta alasannya). -->

- **Sen 19, sanity run Steepest Ascent** (bukan hasil resmi; hasil resmi dari `experiments.py`):
  `main.json` seed 1/2/3 → 982 / 978 / 902 (gap UB 5.1% / 5.5% / 12.9%), 16–20 iterasi, ~1.3 s, semua
  feasible. `small.json` seed 1/2/3 → 199 / 199 / 272, padahal global optimum 287. Dua run terjebak di local
  optimum yang sama (gap 31% dari optimum). Ini contoh bagus untuk analisis kelemahan Steepest Ascent dan
  motivasi Sideways / Random Restart / SA.
- **Sen 19, sanity run varian HC (Bonus 2)**, default params, seed 1/2/3 (bukan hasil resmi):

  | Varian | `main.json` | Durasi | `small.json` (optimum 287) |
  |---|---|---|---|
  | Steepest | 982 / 978 / 902 | ~1.3 s | 199 / 199 / 272 |
  | Sideways (100) | 982 / 978 / 960 | ~9.4 s | 225 / 271 / 277 |
  | Random Restart (10) | 982 / 993 / 946 | ~14.5 s | 277 / 277 / 272 |
  | Stochastic | 778 / 876 / 771 | ~0.3 s | 177 / 155 / 137 |

  Semua feasible. Random Restart terbaik di `main.json` (993, gap UB 4.1%), Stochastic terlemah: di geladak yang
  hampir penuh hampir semua neighbor acak overlap, sehingga hanya 38–53 langkah yang diterima dari ~30 ribu
  iterasi. Sideways baru membantu bila local optimum Steepest berada di plateau (seed 3: 902 → 960).
- **Sel 20, sanity run multi-kapal (Bonus 3)** pada `multi.json`, seed 1 (bukan hasil resmi):

  | Varian | Objective | Gap UB | Durasi | Kendaraan per kapal | Berat per kapal (C = 80 / 54 / 32) |
  |---|---|---|---|---|---|
  | Steepest | 1170 | 11.2% | 3.5 s | 10 / 6 / 5 | 70 / 51 / 30 |
  | Sideways (100) | 1231 | 6.6% | 17.1 s | 9 / 8 / 5 | 78 / 53 / 30 |
  | Random Restart (10) | 1188 | 9.9% | 34.8 s | 8 / 6 / 7 | 80 / 50 / 25 |
  | Stochastic | 974 | 26.1% | 0.2 s | 5 / 6 / 6 | 61 / 50 / 17 |

  Semua feasible dan memakai ketiga kapal. Steepest seed 2/3: 1072 / 1078. Gap UB lebih besar daripada
  `main.json` karena UB armada menggabungkan kapasitas dan luas semua kapal (DESIGN §8).
- **Sen 19, sanity run Simulated Annealing**, default params (§4.5), seed 1/2/3 (bukan hasil resmi):

  | Instance | Objective | Gap UB | Iterasi ke-k objective terbaik pertama kali dicapai | #Stuck | Durasi |
  |---|---|---|---|---|---|
  | `main.json` | 964 / 973 / 962 | 6.9% / 6.0% / 7.1% | 60 862 / 65 868 / 62 170 | 182 / 185 / 179 | ~1.8 s |
  | `small.json` (optimum 287) | 287 / 287 / 287 | 3.7% (= optimum) | 50 893 / 44 092 / 49 451 | 191 / 191 / 192 | ~1.6 s |
  | `multi.json` | 1214 / 1246 / 1214 | 7.9% / 5.5% / 7.9% | 65 076 / 70 425 / 75 639 | 179 / 174 / 178 | ~1.8 s |

  Semua feasible; di `multi.json` ketiga kapal terpakai. `T0` ≈ 8 100–13 200 (`main.json`), besar karena
  penalty satu sel overlap = `P` = 181. SA mengungguli Steepest di `main.json` (mean 966 vs 954) dan menemukan
  optimum `small.json` di ketiga seed, sedangkan Steepest terjebak di 199 / 199 / 272.

  **Tuning `N`** (`main.json` / `multi.json`, mean 5 seed): 20 000 → 922 / 1148, 50 000 → 970 / 1139,
  100 000 → 971 / 1216, 200 000 → 977 / 1217 dengan durasi 2× lipat, jadi dipilih `N = 100000`. `T_min = 1`
  tidak berbeda nyata dari `T_min = 0.01`. Versi awal dengan `α = 0.999` tetap (berhenti saat `T < T_min`,
  ~14 ribu iterasi) hanya mencapai 899 / 924 / 945 di `main.json`, karena suhu turun terlalu cepat.

  **Catatan frekuensi stuck (untuk analisis §5):** objective terbaik terakhir kali naik di ~60–75% run. Sisa
  run berada di suhu rendah (SA praktis menjadi hill-climbing), sehingga 68–78 dari ~180 kejadian stuck di
  `main.json` terjadi setelah titik itu. Dengan definisi DESIGN §7.2 (counter di-reset setiap `K`
  iterasi), jumlah stuck juga mengukur lamanya SA tertahan, bukan hanya berapa kali. Ini perlu ditulis
  eksplisit di laporan.
- **Sel 20, sanity run Genetic Algorithm**, default params (§4.6, pop 100, 1000 generasi), seed 1/2/3 (bukan
  hasil resmi):

  | Instance | Objective | Gap UB | Generasi best pertama kali dicapai | Mean populasi akhir | Durasi |
  |---|---|---|---|---|---|
  | `main.json` | 780 / 908 / 865 | 24.6% / 12.3% / 16.4% | 952 / 866 / 909 | 333 / 52 / −277 | ~1.3 s |
  | `small.json` (optimum 287) | 241 / 287 / 285 | 19.1% / 3.7% / 4.4% | 300 / 317 / 133 | 22 / 68 / 7 | ~0.8 s |
  | `multi.json` | 1016 / 885 / 1032 | 22.9% / 32.9% / 21.7% | 953 / 654 / 964 | −543 / −329 / −309 | ~1.9 s |

  Semua feasible; di `multi.json` ketiga kapal terpakai. GA di bawah Steepest (`main.json` 982 / 978 / 902) dan
  SA. Mean populasi jauh di bawah max dan sering negatif: anak crossover dari dua induk feasible hampir selalu
  overlap (posisi kendaraan saling bergantung, DESIGN §4), sehingga sebagian besar anak terkena penalty.
  Best masih naik sampai generasi akhir.

  **Tuning** (`main.json`, mean 3 seed): pop 50 / 300 gen → 674, pop 100 / 1000 → 851, pop 100 / 3000 → 869
  (3× durasi), pop 200 / 1000 → 875. Variasi `p_m` ∈ {0.1, 0.2, 0.5, 1.0} × elitism ∈ {1, 2, 5} memberi mean
  767–919 tanpa pola yang konsisten (masih dalam noise 3 seed), jadi dipakai nilai DESIGN §7.3.
