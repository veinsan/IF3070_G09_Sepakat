# Design Decisions — Vehicle Deck Loading (Local Search)

Dokumen hidup. Setiap keputusan di sini **harus** dijelaskan ulang di laporan (bab Pembahasan).
Status keputusan: ✅ final · 🟡 usulan (perlu disepakati / dikonfirmasi asisten).

---

## 1. Formalisasi Masalah

- Geladak (deck): grid `W × L`, kapasitas berat `C`.
- Kendaraan `i = 1..n`: `w_i × l_i`, `fee_i`, `weight_i`, `eta_i`, orientasi ∈ {H, V}.
- Keputusan: untuk tiap kendaraan → **di luar kapal** ATAU (x, y, orientasi) di dalam geladak.
- Maksimalkan `Σ fee_i` kendaraan yang dimuat.
- Constraint: (1) no overlap, (2) di dalam batas geladak, (3) `Σ weight_i ≤ C`.

> Catatan: spec masih menyebut "truk", "peti kemas", "paket" (sisa spec tahun lalu). Kita anggap
> truk = kapal, peti kemas = geladak, paket = kendaraan. 🟡 Konfirmasi di Teams.
> `ETA` tidak dipakai di objective wajib, jadi kita pakai untuk **Bonus 1**.

## 2. Format Input (JSON) 🟡

```json
{
  "ships": [
    { "id": "Deck-1", "width": 10, "length": 20, "max_capacity": 500 }
  ],
  "vehicles": [
    { "id": "Owen", "width": 3, "length": 4, "shipping_fee": 60, "weight": 5, "eta": 3 }
  ]
}
```

`ships` sengaja berupa list sejak awal. Single-ship = list berisi 1 elemen, jadi Bonus 3 (multi-kapal)
tidak butuh refactor.

**Validasi** (`core/problem.py`, pesan error menunjuk lokasi, misalnya `vehicles[3].width`):

| Field | Aturan |
|---|---|
| `ships`, `vehicles` | list tidak kosong, `id` string unik |
| `width`, `length` | bilangan bulat ≥ 1 |
| `max_capacity`, `weight` | angka > 0 (berat > 0 dibutuhkan oleh properti penalty §4) |
| `shipping_fee` | angka ≥ 0 |
| `eta` | bilangan bulat ≥ 0 |

Key lain (`meta`, `type`, dll.) diabaikan supaya instance dari asisten tetap terbaca.

**Generator** (`core/generator.py`): kendaraan dari katalog 6 tipe (motor 1×2, sedan 2×4, SUV 2×5,
pickup 2×6, truk 3×8, bus 3×10) dengan fee/berat acak per rentang tipe. Kapasitas =
`capacity_ratio` (default 0.8) × luas geladak × rata-rata berat per sel, sehingga geladak **tidak bisa
diisi penuh** dan constraint berat ikut aktif (kalau kapasitas dibuat dari total berat, constraint berat
hampir tidak pernah aktif karena luas habis duluan). Parameter generator disimpan di `meta` instance.

| Instance | Perintah | Isi |
|---|---|---|
| `src/data/main.json` | `--seed 1 --vehicles 30 --width 10 --length 20` | luas 466/200 (2.33×), berat 382/131 (2.92×), fee total 2351 |
| `src/data/small.json` | `--seed 2 --vehicles 7 --width 4 --length 6 --types motor sedan suv` | luas 38/24 (1.58×), berat 26/13 (2.00×), untuk brute force |

## 3. Representasi State ✅ (`core/state.py`)

Satu gene per kendaraan (urutan index tetap):

```
pos[i] = None                      # di luar kapal
pos[i] = (ship, x, y, orient)      # anchor = sel kiri-atas, orient ∈ {H, V}
```

- `H`: menempati `w_i` kolom × `l_i` baris. `V`: di-rotate (`l_i` × `w_i`). Konvensi ini ditulis di laporan.
- Koordinat integer, `0 ≤ x < W`, `0 ≤ y < L`.
- Representasi yang sama dipakai HC, SA, dan GA (jadi GA chromosome = list `pos`).
- Anchor acak selalu di dalam geladak, tapi badan kendaraan boleh keluar (dihitung sebagai pelanggaran).
- Untuk evaluasi cepat: simpan `occupancy[ship][y * W + x]` (list datar per kapal) = jumlah kendaraan
  di sel itu, plus agregat overlap, out-of-bound, fee, dan berat per kapal.
- **Initial state** (`random_state`): tiap kendaraan masuk ke kapal/anchor/orientasi acak dengan peluang
  `p_inside` (default 0.5), sisanya di luar. Tidak ada perbaikan greedy, sesuai spek "inisialisasi random".
- State bisa diserialisasi ke JSON (`to_dict`/`from_dict`): per kendaraan `{id, ship, x, y, orientation}`,
  `ship = null` untuk kendaraan di luar.

**Kenapa pakai koordinat eksplisit (bukan permutasi + decoder bottom-left)?** Tiga move di spec
("pindah ke koordinat", "tukar", "ubah orientasi") itu operasi terhadap koordinat, jadi
representasi ini map 1:1 ke spec.

## 4. Objective Function ✅ (`core/objective.py`)

```
f(s) = Σ_{i dimuat} fee_i − P · (overlap_cells + out_of_bound_cells + weight_units)

overlap_cells      = Σ_cells max(0, occupancy − 1)
out_of_bound_cells = jumlah sel kendaraan yang keluar batas geladak
weight_units       = Σ_kapal ceil( max(0, Σ_{i di kapal} weight_i − C_kapal) / w_min )
w_min              = berat kendaraan teringan
P                  = max_i(fee_i) + 1
```

**Kenapa penalty, bukan hanya state feasible?**
1. Crossover GA hampir pasti menghasilkan anak dengan overlap, jadi GA tetap butuh penalty.
   Kalau satu fungsi dipakai untuk ketiga algoritma, perbandingannya fair.
2. SA bisa melewati daerah infeasible sebentar untuk kabur dari local optimum.
3. **Properti penting (tulis di laporan):** karena `P > max fee`, dari state infeasible mana pun,
   mengeluarkan kendaraan yang melanggar **pasti** menaikkan `f` (penalty turun ≥ P, fee turun
   < P). Jadi **tidak ada state infeasible yang jadi local optimum** untuk HC dengan neighborhood
   penuh, dan hasil akhir HC pasti feasible. Properti ini diuji di
   `tests/test_state.py::test_infeasible_state_always_has_improving_removal`.
4. **Kenapa berat dibagi `w_min` lalu dibulatkan ke atas?** Berat boleh pecahan (DESIGN §2). Dengan
   `max(0, Σw − C)` biasa, mengeluarkan kendaraan seberat 0.5 hanya menurunkan penalty 0.5·P (< fee),
   sehingga state kelebihan berat bisa menjadi local optimum. Dengan `ceil(excess / w_min)`, mengeluarkan
   kendaraan mana pun (berat ≥ `w_min`) dari kapal yang kelebihan berat menurunkan `weight_units`
   minimal 1, jadi penalty turun ≥ P. Untuk `w_min = 1` (misalnya `main.json`, yang punya motor seberat 1),
   rumus ini sama dengan kelebihan berat biasa. Perbandingan berat memakai toleransi `1e-9` agar noise
   float tidak dihitung sebagai pelanggaran.

Yang dicatat di output: `objective`, `total_fee`, `is_feasible`, `used_weight`, `used_area_pct`.

**Delta evaluation (heuristik performa):** move hanya mengubah 1–2 kendaraan, jadi hitung ulang
cukup untuk sel-sel yang disentuh (update `occupancy`), bukan seluruh grid. `State.delta(changes)`
menerapkan perubahan, membaca objective dari agregat (O(jumlah kapal)), lalu membatalkannya.
`core.objective.evaluate()` menghitung semuanya dari nol dan menjadi acuan: test membandingkan keduanya
di 3000 move acak per instance. Terukur ~5 µs per `delta()` di `main.json`, jadi satu iterasi Steepest
Ascent (~12.5 ribu neighbor) ≈ 0.07 s.

## 5. Neighbor Moves ✅ (sesuai spec)

| Move | Definisi |
|---|---|
| `move(i, pos')` | Pindahkan kendaraan `i` ke koordinat lain, **termasuk ke "luar kapal"** (`None`) atau dari luar ke dalam |
| `swap(i, j)` | Tukar anchor `pos` dua kendaraan (orientasi masing-masing tetap). Berlaku dalam↔dalam, dalam↔luar |
| `rotate(i)` | Toggle H↔V, anchor tetap. Hanya untuk kendaraan yang di dalam |

- **Full neighborhood** (untuk Steepest Ascent): semua `move` (n × (W·L·2 + 1)) + semua `swap` (n(n−1)/2) + semua `rotate` (n).
- **Random neighbor** (untuk Stochastic HC, SA, mutasi GA): pilih tipe move secara uniform, lalu parameternya secara random.

## 6. Referensi Global Optimum (untuk analisis "seberapa dekat ke global optima")

Global optimum sebenarnya susah dihitung. Kita pakai **upper bound**:
- 0/1 knapsack 2 dimensi (berat ≤ C, total luas ≤ W·L) via DP, dengan geometri diabaikan.
- `UB ≥ optimum sebenarnya`, jadi `gap = (UB − f) / UB` adalah **batas atas** gap yang sebenarnya.
- Opsional: 1 instance kecil (≤ 6 kendaraan, deck kecil) di-brute force untuk global optimum yang
  pasti, supaya bisa dibandingkan dengan UB.

## 7. Algoritma

### 7.1 Hill-Climbing (wajib min. 1, Bonus 2: semua)

Cek definisinya lagi ke salindia Khodra (spec: "utamakan implementasi yang mengacu pada salindia").

| Varian | Aturan | Stop | Yang dicatat (spec) |
|---|---|---|---|
| Steepest Ascent | ambil neighbor terbaik, pindah kalau `>` current | tidak ada neighbor lebih baik | iterasi |
| Stochastic | ambil neighbor random, pindah kalau `>` current | `max_iter` atau `max_no_improve` berturut | iterasi |
| Sideways Move | Steepest, tapi boleh pindah kalau `==` | `max_sideways` tercapai 🟡 (berturut-turut vs total, konfirmasi) | iterasi, `max_sideways` |
| Random Restart | Steepest dari initial random baru | `max_restart` tercapai | jumlah restart, iterasi per restart, `max_restart` |

### 7.2 Simulated Annealing

- Terima neighbor lebih baik; kalau lebih buruk, terima dengan peluang `e^(ΔE/T)` (ΔE < 0).
- **Schedule:** geometric `T_k = T0 · α^k`, contoh `α = 0.995`; stop saat `T < T_min` atau `max_iter`.
- **T0 heuristik:** sampling ~100 random move yang memperburuk, lalu `T0 = −mean(ΔE) / ln(0.8)`
  (awalnya ~80% move buruk diterima). Sebutkan sumbernya di laporan.
- **Plot `e^(ΔE/T)`:** catat hanya di iterasi dengan ΔE < 0 (untuk ΔE ≥ 0 nilainya 1 dan tidak informatif).
- **Definisi "stuck" 🟡:** 1 kejadian stuck = nilai `best` tidak membaik selama `K` iterasi
  berturut-turut (contoh `K = 500`), lalu counter di-reset. Frekuensi = jumlah kejadian.
  Definisi ini **wajib** ditulis eksplisit di laporan.

### 7.3 Genetic Algorithm — **Roulette Wheel Selection (WAJIB, BUKAN tournament)**

- **Chromosome:** list `pos` (sama seperti state).
- **Fitness:** `f(s)` bisa negatif karena ada penalty, padahal roulette butuh nilai ≥ 0. Pakai windowing:
  `fit_i = f_i − min_j f_j + ε` (ε kecil, misal 1). Tulis alasannya di laporan.
- **Selection (roulette / spin wheel):** `p_i = fit_i / Σ fit`. Buat cumulative sum, lalu spin
  `r ~ U(0, Σfit)` dan pilih individu pertama dengan `cumsum ≥ r` (`bisect`). Implementasi eksplisit,
  jangan cuma `random.choices`, supaya roda "spin"-nya jelas kelihatan waktu demo dan di laporan.
  Sesuai salindia GA Khodra.
- **Crossover:** one-point crossover pada index kendaraan, `p_c` tetap (misal 0.8).
- **Mutation:** dengan `p_m` (misal 0.1–0.2) terapkan satu random move (move/swap/rotate).
- **Elitism:** bawa 1–2 individu terbaik ke generasi berikut. Ini heuristik tambahan, jelaskan di laporan.
- **Parameter yang divariasikan (spec):** hanya `population_size` dan `iterations` (= generasi).
  Parameter lain (`p_c`, `p_m`, elitism) dibuat **tetap** di semua eksperimen.
- **Dicatat per generasi:** `max` dan `mean` objective populasi.

## 8. Bonus

| Bonus | Poin | Desain |
|---|---|---|
| 1. Objective alternatif (tanpa variabel baru) | 3 | Prioritas ETA: `Σ fee_i · (1 + 1/eta_i)` (makin mendesak, makin berbobot). Jalankan ulang 1 set eksperimen untuk dibandingkan |
| 2. Semua varian HC | 7 | Tabel 7.1, masing-masing 3 run |
| 3. Multi-kapal | 10 | `pos` sudah punya `ship`; constraint per kapal; `move` boleh ke kapal lain; `swap` lintas kapal; UB pakai total kapasitas & luas |

Urutan pengerjaan yang disarankan: Bonus 2 → Bonus 1 → Bonus 3, **setelah** semua spek wajib selesai.

## 9. Keputusan Terbuka

- [x] Konstanta penalty `P` final (`max fee + 1`, berat via `weight_units`)
- [ ] `max_sideways` berturut-turut atau total
- [ ] Definisi "stuck" SA disepakati
- [ ] Nilai default SA (`α`, `T_min`, `max_iter`) dan GA (`p_c`, `p_m`, elitism)
- [ ] Format input dikonfirmasi (apakah asisten kasih test case sendiri saat demo?)

## 10. Struktur Kode & Konvensi ✅

Struktur lengkap per file ada di [README](../README.md#struktur-repository). Pembagian layer:

| Layer | Folder | Tanggung jawab | Boleh import |
|---|---|---|---|
| Model | `src/core/` | Data persoalan, state, objective, delta evaluation, upper bound | stdlib saja |
| Search | `src/search/` | Neighbor + HC, SA, GA. Hanya bicara ke API `State` | `core` |
| Visualisasi | `src/visualization/` | Gambar state + plot. Membaca dict hasil / JSON di `output/`, tidak menjalankan search | `core`, `matplotlib` |
| Entry point | `src/main.py`, `src/experiments.py` | CLI + runner eksperimen | semua |
| Analisis | `notebooks/experiments.ipynb` | Tabel + plot dari `output/*.json` | `src` (via `sys.path`) |

Alasan: algoritma tidak tahu detail grid, jadi delta evaluation dan multi-kapal (Bonus 3) cukup diubah di
`core/`. Visualisasi dibuat dari JSON, jadi plot bisa dibuat ulang tanpa run ulang (EXPERIMENTS §2).

**Konvensi:**
- Program dijalankan dari root repo (`python src/main.py ...`), import absolut dari `src/`
  (`from core.state import State`).
- Identifier dalam bahasa Inggris. Docstring modul + fungsi publik, serta komentar, dalam bahasa Indonesia.
- Type hints di semua fungsi publik.
- **Tidak ada RNG global.** Setiap fungsi acak menerima `rng: random.Random` sehingga run dengan seed
  yang sama selalu identik.
- Semua algoritma mengembalikan format hasil yang sama (`search/result.py`, EXPERIMENTS §2).
- Kode yang diadaptasi dari internet diberi komentar `# Sumber: <judul>, <url>` (aturan spek) dan
  dicantumkan di referensi laporan.
- Logika non-trivial punya test di `tests/` (stdlib `unittest`, tanpa dependency tambahan):
  `python -m unittest discover -s tests -t .`
