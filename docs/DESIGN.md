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

> Catatan: spec v1.1 (07/10/2026) sudah mengganti "truk" menjadi "kapal". Sisa istilah "peti kemas" dan
> "paket" (dari spec tahun lalu) kita anggap peti kemas = geladak, paket = kendaraan. 🟡 Konfirmasi di Teams.
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
| `src/data/small.json` | `--seed 3 --vehicles 12 --width 6 --length 8 --capacity-ratio 1.0 --types motor sedan suv pickup` | luas 88/48 (1.83×), berat 62/34 (1.82×), fee total 493, untuk brute force (§6) |

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
  `ship = null` untuk kendaraan di luar, ditambah `decks[].grid[y][x]` (id kendaraan per sel, `"A+B"` bila
  overlap). Grid hanya turunan untuk dibaca dan divisualisasi, `from_dict` mengabaikannya.
- Hasil satu run dibungkus `RunResult` (`search/result.py`), format lengkapnya di EXPERIMENTS §2.

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

## 5. Neighbor Moves ✅ (`search/neighbors.py`)

| Move | Definisi |
|---|---|
| `move(i, pos')` | Pindahkan kendaraan `i` ke koordinat lain, **termasuk ke "luar kapal"** (`None`) atau dari luar ke dalam |
| `swap(i, j)` | Tukar anchor (kapal, x, y) dua kendaraan, orientasi masing-masing tetap. Berlaku dalam↔dalam dan dalam↔luar. Kendaraan yang masuk dari luar memakai orientasi pasangannya (karena kendaraan di luar tidak punya orientasi) |
| `rotate(i)` | Toggle H↔V, anchor tetap. Hanya untuk kendaraan di dalam yang **tidak persegi** (rotasi persegi menempati sel yang sama) |

Satu move = list perubahan `[(i, placement), ...]` yang langsung dipakai `State.delta()` / `State.apply()`.

- **Full neighborhood** (`all_neighbors`, untuk Steepest Ascent), tanpa duplikat dan tanpa no-op:
  - `move`: tiap kendaraan ke semua placement `S·W·L·2`. Kendaraan di dalam melewati placement dengan
    anchor yang sama (orientasi lain = `rotate`), ditambah satu move ke luar.
  - `swap`: semua pasangan, kecuali pasangan yang sama-sama di luar atau yang hasilnya tidak berubah.
  - `rotate`: kendaraan di dalam yang tidak persegi.
  - `main.json`: ~12.3 ribu neighbor, satu iterasi Steepest (enumerasi + `delta`) ≈ 0.07 s.
- **Random neighbor** (`random_neighbor`, untuk Stochastic HC, SA, mutasi GA): tipe move dipilih uniform
  dari {move, swap, rotate}, lalu parameternya acak. Bila tipe tidak mungkin (misalnya tidak ada kendaraan
  di dalam untuk di-swap/rotate), dipakai `move`. ≈ 9 µs per neighbor + `delta`.
  - **Heuristik:** untuk `move` kendaraan yang di dalam, target "ke luar" dan "ke koordinat acak" masing-masing
    berpeluang 1/2. Kalau target dipilih uniform dari semua `2·W·L + 1` kemungkinan, peluang keluar hanya
    1/401 di `main.json`, sehingga kendaraan yang melanggar constraint hampir tidak pernah dikeluarkan oleh
    SA/Stochastic HC. Tulis heuristik ini di laporan.

## 6. Referensi Global Optimum ✅ (`core/bounds.py`)

Global optimum `main.json` (30 kendaraan) terlalu mahal untuk dihitung persis. Kita pakai **upper bound**:
- **UB** (`upper_bound`): 0/1 knapsack 2 dimensi (total berat ≤ ΣC, total luas ≤ Σ W·L) via DP
  `best[luas][berat]`, dengan geometri diabaikan. Kendaraan yang tidak muat di geladak mana pun
  (dalam orientasi apa pun) dibuang. Berat dan kapasitas dibulatkan ke bawah: untuk himpunan feasible,
  `Σ floor(w) ≤ Σ w ≤ C`, jadi `Σ floor(w) ≤ floor(C)`. Relaksasi tetap valid untuk berat pecahan dan persis
  untuk berat bulat. Multi-kapal (Bonus 3) memakai total kapasitas dan total luas.
- `UB ≥ optimum sebenarnya`, jadi `gap = (UB − f) / UB` adalah **batas atas** gap yang sebenarnya.
- **Brute force** (`brute_force`): backtracking per kendaraan (di luar, atau tiap posisi yang masih feasible)
  dengan sel terpakai sebagai bitmask, ditambah branch and bound: cabang dipotong bila
  `fee sekarang + fee semua kendaraan sisa ≤ terbaik`. Kendaraan ber-fee besar dicoba dulu. Ada batas
  `max_nodes` supaya tidak macet di instance besar.

| Instance | UB | Global optimum | UB longgar | Waktu |
|---|---|---|---|---|
| `main.json` | **1035** | tidak dihitung | – | UB 0.02 s |
| `small.json` | 298 | **287** (brute force) | 3.7% | brute force 0.2 s |

**Temuan untuk laporan (seberapa longgar UB):** pada instance kecil acak, UB = optimum persis bila yang
membatasi adalah berat (kendaraan kecil mudah disusun rapat). Bila kapasitas berat dibuat longgar sehingga
geometri yang membatasi (misalnya sedan/SUV/pickup di deck 5×7), UB lebih tinggi 5–23% dari optimum,
karena sisa sel yang "terfragmentasi" tidak bisa dipakai. Di `main.json` keduanya membatasi, jadi gap terhadap
UB sebaiknya dibaca sebagai batas atas, bukan jarak pasti ke optimum. `small.json` dipakai untuk
membandingkan hasil algoritma terhadap global optimum yang pasti.

Kebenaran diuji di `tests/test_bounds.py`: UB = enumerasi semua subset, brute force = enumerasi semua state
pada instance mungil, dan optimum ≤ UB pada instance acak.

## 7. Algoritma

### 7.1 Hill-Climbing (wajib min. 1, Bonus 2: semua)

Cek definisinya lagi ke salindia Khodra (spec: "utamakan implementasi yang mengacu pada salindia").

| Varian | Aturan | Stop | Yang dicatat (spec) |
|---|---|---|---|
| Steepest Ascent | ambil neighbor terbaik, pindah kalau `>` current | tidak ada neighbor lebih baik | iterasi |
| Stochastic | ambil neighbor random, pindah kalau `>` current | `max_no_improve` neighbor berturut-turut tidak lebih baik, atau `max_iterations` | iterasi |
| Sideways Move | Steepest, tapi boleh pindah kalau `==` | semua neighbor `<` current, atau **total** sideways move mencapai `max_sideways` | iterasi, `max_sideways` |
| Random Restart | Steepest dari initial random baru | banyak restart mencapai `max_restart` | jumlah restart, iterasi per restart, `max_restart` |

**Steepest Ascent ✅ (`search/hill_climbing.py`):**
- Sesuai salindia: tiap iterasi mengevaluasi seluruh neighborhood (§5) dengan `State.delta`, lalu pindah ke
  neighbor terbaik hanya bila `Δ > 0`. Berhenti di local optimum (`extra.stop_reason = "local_optimum"`).
- **1 iterasi = 1 langkah pindah**, jadi `history.objective` berisi `iterations + 1` nilai (indeks 0 = state
  awal). Evaluasi neighborhood terakhir yang tidak menemukan perbaikan tidak dihitung sebagai iterasi, tapi
  ikut dihitung di `evaluations`.
- **Tie-breaking acak (heuristik):** bila beberapa neighbor sama-sama terbaik, dipilih acak dengan peluang sama
  (reservoir sampling). Tanpa ini, `move` selalu menang karena dienumerasi lebih dulu dari `swap`/`rotate`.
- `max_iterations` (default 10 000, `config.HC_MAX_ITERATIONS`) hanya pengaman, bukan bagian algoritma. Di
  `main.json` Steepest berhenti sendiri setelah ~20 iterasi.
- Karena neighborhood lengkap dan `P > max fee` (§4), state akhir **selalu feasible**. Ini diuji di
  `tests/test_hill_climbing.py`, beserta pengecekan bahwa state akhir memang local optimum.
- `best_neighbor()` dipisah supaya bisa dipakai ulang oleh Sideways Move dan Random Restart (Bonus 2).

**Varian lain ✅ (Bonus 2, `search/hill_climbing.py`):** Steepest, Sideways, dan Random Restart memakai satu
loop pendakian yang sama (`_climb`). Steepest Ascent = Sideways dengan `max_sideways = 0`.

- **Sideways Move** (`sideways_move`, default `max_sideways = 100`):
  - Pindah ke neighbor terbaik bila `Δ > 0` (naik) atau `Δ = 0` (sideways, untuk keluar dari shoulder/plateau).
    Sideways move dipilih acak di antara neighbor terbaik yang setara (tie-break §7.1).
  - **`max_sideways` dihitung total sepanjang run**, bukan berturut-turut. Alasannya kalimat spesifikasi:
    "ketika banyak *sideways move* yang dilakukan sudah mencapai maksimum, pencarian dihentikan". Yang dihitung
    adalah banyaknya sideways move yang **sudah dilakukan**, tanpa syarat berturut-turut, dan pencarian
    **langsung berhenti** saat jumlahnya mencapai maksimum (`stop_reason = "max_sideways"`). Selain itu berhenti
    di local optimum ketat, yaitu semua neighbor `< current` (`"local_optimum"`).
  - Dicatat: `iterations` (langkah naik + sideways), `params.max_sideways`, `extra.sideways_moves`.
- **Random Restart** (`random_restart`, default `max_restart = 10`):
  - 1 percobaan awal + `max_restart` restart, masing-masing Steepest Ascent dari initial state acak baru (RNG
    yang sama, jadi tetap reproducible). Percobaan pertama identik dengan Steepest Ascent seed yang sama, sehingga
    hasilnya **selalu ≥** Steepest Ascent. Hasil akhir = state terbaik dari semua percobaan.
  - `history.objective` = semua percobaan disambung (pola gigi gergaji), `history.best` = terbaik sejauh ini.
    Lompatan ke initial state baru dihitung satu iterasi, jadi `iterations = Σ iters_per_restart + restarts`.
  - Dicatat: `extra.restarts`, `extra.iters_per_restart`, `extra.final_objective_per_restart`,
    `extra.best_restart`, `params.max_restart`.
- **Stochastic** (`stochastic`, default `max_no_improve = 20 000`, `max_iterations = 200 000`):
  - Tiap iterasi mengambil satu neighbor acak (`random_neighbor`, §5) dan pindah hanya bila `Δ > 0`.
    1 iterasi = 1 neighbor dievaluasi, jadi `evaluations = iterations`.
  - `max_no_improve` ≈ 1.6 × ukuran neighborhood `main.json` (~12.3 ribu), supaya peluang melewatkan neighbor
    yang lebih baik kecil sebelum dianggap local optimum.
  - State akhir **tidak dijamin** feasible (berbeda dengan Steepest), karena neighbor yang memperbaiki pelanggaran
    bisa saja tidak pernah terambil. Di semua sanity run hasilnya tetap feasible.
  - Dicatat: `iterations`, `extra.improvements` (banyak langkah yang diterima), `extra.stop_reason`.

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
| 1. Objective alternatif (tanpa variabel baru) | 3 | Prioritas ETA: `Σ fee_i · (1 + 1/eta_i)` (makin mendesak, makin berbobot). Jalankan ulang 1 set eksperimen untuk dibandingkan. ⚠ `eta` boleh 0 (§2), jadi rumusnya perlu dijaga dari pembagian nol (misalnya `1/(eta_i + 1)`). `P` juga harus memakai bobot maksimum, bukan fee maksimum, supaya properti §4 tetap berlaku |
| 2. Semua varian HC | 7 | Tabel 7.1, masing-masing 3 run |
| 3. Multi-kapal | 10 | `pos` sudah punya `ship`; constraint per kapal; `move` boleh ke kapal lain; `swap` lintas kapal; UB pakai total kapasitas & luas |

**Status Bonus 3 (per Sen 19):** core sudah mendukung banyak kapal sejak fondasi: occupancy dan berat per
kapal (`State`), `all_placements`/`random_placement` mencakup semua kapal sehingga `move` dan `swap` bisa lintas
kapal, UB memakai total kapasitas dan luas, dan `brute_force` menangani banyak kapal. Semua itu sudah teruji
dengan instance 2 kapal di `tests/test_state.py`. Yang tersisa: opsi multi-kapal di generator, instance
`src/data/multi.json`, test end-to-end, dan visualisasi beberapa geladak.

Urutan pengerjaan dan pemotongan bila waktu kurang ada di PROJECT_TRACKER §Jadwal.

## 9. Keputusan Terbuka

- [x] Konstanta penalty `P` final (`max fee + 1`, berat via `weight_units`)
- [x] `max_sideways` berturut-turut atau total → **total**, langsung berhenti saat tercapai (§7.1)
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
