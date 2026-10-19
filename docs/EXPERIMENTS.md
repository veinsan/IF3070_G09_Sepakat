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

## 2. Format Output per Run

`output/<algo>/<run_id>.json`, contoh `output/ga/pop50_iter300_seed2.json`:

```json
{
  "algorithm": "ga", "instance": "main.json", "seed": 2,
  "params": { "population": 50, "iterations": 300, "p_c": 0.8, "p_m": 0.1, "elitism": 2 },
  "initial_state": { "...": "..." }, "final_state": { "...": "..." },
  "initial_objective": 0, "final_objective": 0, "total_fee": 0, "is_feasible": true,
  "duration_s": 0.0, "evaluations": 0,
  "history": { "objective": [], "mean": [], "prob": [] },
  "extra": { "iterations": 0, "restarts": 0, "iters_per_restart": [], "stuck_count": 0 }
}
```

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

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | Evals | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |
| **mean ± std** | | | | | | | | | |

### 4.2 Hill-Climbing — Stochastic (Bonus 2 jika bukan varian utama)

Params: `max_iter = __`, `max_no_improve = __`

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | Evals | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

### 4.3 Hill-Climbing — Sideways Move

Params: `max_sideways = __`

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | #Sideways | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | | | | | | | | |
| 2 | 2 | | | | | | | | |
| 3 | 3 | | | | | | | | |

### 4.4 Hill-Climbing — Random Restart

Params: `max_restart = __`

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
