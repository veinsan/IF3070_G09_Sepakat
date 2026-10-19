# Experiments Log

Semua run **harus reproducible**: instance tetap, seed tercatat, output mentah disimpan di `output/`.

## 1. Protokol

- **Instance utama:** `src/data/main.json` (n kendaraan = 30, deck = 10×20, C = 131, generator seed 1; lihat DESIGN §2).
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

Params: `T0 = __ (auto)`, `α = __`, `T_min = __`, `max_iter = __`, stuck window `K = __`

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | #Stuck | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

Plot per run: objective vs iterasi, dan `e^(ΔE/T)` vs iterasi.

### 4.6 GA — Kontrol Populasi (pop = __), Variasi Iterasi

Fixed: `p_c = __`, `p_m = __`, elitism `= __`, selection = **roulette wheel**

| Iterasi | Run | Seed | Obj akhir (best) | Fee | Feasible | Gap UB | Durasi (s) |
|---|---|---|---|---|---|---|---|
| __ (rendah) | 1–3 | 1,2,3 | | | | | |
| __ (sedang) | 1–3 | 1,2,3 | | | | | |
| __ (tinggi) | 1–3 | 1,2,3 | | | | | |

Saran awal: pop = 50, iterasi ∈ {100, 300, 1000}. Sesuaikan dengan runtime.

### 4.7 GA — Kontrol Iterasi (iter = __), Variasi Populasi

| Populasi | Run | Seed | Obj akhir (best) | Fee | Feasible | Gap UB | Durasi (s) |
|---|---|---|---|---|---|---|---|
| __ (kecil) | 1–3 | 1,2,3 | | | | | |
| __ (sedang) | 1–3 | 1,2,3 | | | | | |
| __ (besar) | 1–3 | 1,2,3 | | | | | |

Saran awal: iter = 300, pop ∈ {20, 50, 100}.
Plot per run: **max** dan **mean** objective populasi vs generasi.

### 4.8 Ringkasan Antar-Algoritma

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
