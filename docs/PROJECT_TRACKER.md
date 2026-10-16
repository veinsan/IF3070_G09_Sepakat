# Project Tracker — Tubes 1 IF3070 (G09)

| | |
|---|---|
| **Deadline** | Kamis, 22 Oktober 2026, **22.22 WIB** (release GitHub + submit di Edunex) |
| **Target freeze internal** | Rabu, 21 Oktober 2026 (buffer 1 hari) |
| **Kelompok** | G09 — **Sepakat** |
| **Repo** | [`veinsan/IF3070_G09_Sepakat`](https://github.com/veinsan/IF3070_G09_Sepakat) (GitHub akun pribadi Riantama, **public** sebelum deadline) |
| **Tag release** | `v1.0` (milestone 1, revisi 0). Revisi berikutnya `v1.1`, `v1.2`, … |
| **Demo** | Jadwal menyusul, pantau Teams |

## Anggota

| Kode | NIM | Nama | Fokus utama |
|---|---|---|---|
| **R** | 18224061 | Riantama Putra | Core model (state, occupancy, objective + penalty, delta evaluation, moves, UB) + seluruh varian Hill-Climbing + Bonus 3 (multi-kapal) |
| **T** | 18224059 | Tiara Kusuma Wardhani | Simulated Annealing + Genetic Algorithm (roulette) + Bonus 1 (objective ETA) |
| **L** | 18224057 | Levina Nathania Bunardi | Input/loader + generator instance + visualisasi + CLI + experiment runner & plot + koordinator laporan |

Kode `[R]`/`[T]`/`[L]` di milestone = penanggung jawab task. `[All]` = dikerjakan bersama.
Semua anggota menulis bagian laporan untuk algoritma masing-masing dan ikut analisis.

**Urutan dependensi:** `[L]` loader + `main.json` dan `[R]` core model harus jadi duluan, karena SA, GA,
visualisasi, dan runner bergantung ke API state/objective/move. Sambil menunggu, `[T]` dan `[L]` bisa
mulai dari kontrak API di DESIGN §3–§5.

---

## Milestones

### M0 — Setup (25–27 Sep) ✅
- [x] Isi sheet kelompok (**batas Minggu 27 Sep 23.59**) → dapat nomor kelompok final (G09)
- [x] Rename repo/folder sesuai format `IF3070_GXX_NamaKelompok`, invite anggota
- [x] Struktur folder: `src/`, `docs/`, `output/`, `README.md`, `.gitignore` (`__pycache__/`, `.venv/`)
- [ ] Baca Q&A di unggahan Teams, lalu kirim pertanyaan terbuka (lihat §Q&A) — ditunda
- [x] Tonton ulang / baca salindia Khodra: HC, SA, GA

### M1 — Core Model (28 Sep – 4 Okt)
- [ ] `[L]` Format input JSON + loader + validasi (DESIGN §2)
- [ ] `[L]` Generator instance random (seeded) + `src/data/main.json` + 1 instance kecil untuk brute force
- [ ] `[R]` State + occupancy grid + objective dengan penalty (DESIGN §4)
- [ ] `[R]` Delta evaluation + 1 self-check (hasil delta = hasil full recompute di ribuan random move)
- [ ] `[R]` 3 move: move (termasuk ke luar), swap, rotate + random neighbor + full neighborhood
- [ ] `[R]` Random initial state
- [ ] `[R]` Upper bound (DP knapsack berat+luas) + brute force instance kecil
- [ ] `[L]` Visualisasi state: grid deck, kendaraan berwarna + label id, daftar kendaraan di luar, nilai objective/fee/berat

### M2 — Algoritma (5–11 Okt)
- [ ] `[R]` Steepest Ascent HC
- [ ] `[T]` SA: T0 otomatis, geometric cooling, catat `e^(ΔE/T)` dan stuck count
- [ ] `[T]` GA: **roulette wheel selection eksplisit** (cumsum + spin), one-point crossover, mutation, elitism
- [ ] `[All]` Semua algoritma return format hasil yang sama (EXPERIMENTS §2)
- [ ] `[L]` CLI: `python src/main.py --algo <hc|sa|ga|...> --instance ... --seed ...`
- [ ] `[R]` (Bonus 2) Stochastic, Sideways, Random Restart HC

### M3 — Eksperimen (12–16 Okt)
- [ ] `[L]` Script `experiments.py` untuk menjalankan semua run wajib (24) → `output/`
- [ ] `[L]` Generate semua plot dari JSON
- [ ] `[All]` Isi tabel di `EXPERIMENTS.md` (masing-masing untuk algoritmanya)
- [ ] `[All]` Sanity check: semua hasil akhir feasible? durasi masuk akal?

### M4 — Laporan, Bonus, Release (17–21 Okt)
- [ ] `[L]` Laporan PDF (koordinator; isi per bab oleh pemilik bagian, lihat checklist di bawah)
- [ ] `[T]` Bonus 1 / `[R]` Bonus 3 kalau waktunya cukup
- [ ] `[L]` README final (setup, run, pembagian tugas)
- [ ] `[R]` Repo **public**, tag `v1.0`, buat GitHub Release (repo di akun Riantama), submit di Edunex
- [ ] `[L]` Clone ulang repo di folder bersih, ikuti README dari nol, pastikan jalan

### M5 — Demo (TBA)
- [ ] Isi jadwal demo
- [ ] Siapkan skenario demo: load instance → run tiap algoritma → tampilkan initial/final state + plot
- [ ] Semua anggota paham seluruh kode (bukan cuma bagiannya sendiri)

---

## Compliance Checklist (dari spec)

### Repository
- [ ] Nama repo `IF3070_GXX_NamaKelompok`, GitHub akun pribadi, **public** saat pengumpulan
- [ ] `src/` source code (**Python** untuk local search)
- [ ] `docs/` laporan **.pdf**
- [ ] `output/` hasil run algoritma
- [ ] `README.md`: deskripsi singkat, cara setup & run, pembagian tugas
- [ ] Release dengan tag format **`vX.Y`** sebelum deadline
- [ ] Semantic commit + branching (commit tiap anggota terlihat)
- [ ] Sumber dari internet dicantumkan **sebagai komentar di kode** dan di referensi laporan

### Implementasi
- [ ] Initial state random
- [ ] Move: tukar 2 kendaraan (dalam/luar), pindah ke koordinat lain, ubah orientasi
- [ ] Constraint: no overlap, dalam batas geladak, berat ≤ kapasitas
- [ ] Objective: maksimalkan total ShippingFee
- [ ] ≥1 Hill-Climbing
- [ ] Simulated Annealing
- [ ] Genetic Algorithm dengan **roulette wheel selection**
- [ ] State menampilkan: kendaraan di dalam & di luar, keadaan geladak, value
- [ ] Visualisasi initial state, final state, dan hasil eksperimen

### Data per run (lihat EXPERIMENTS.md)
- [ ] Semua algoritma: state awal & akhir, objective akhir, plot objective vs iterasi, durasi
- [ ] Steepest / Stochastic HC: jumlah iterasi
- [ ] Sideways: jumlah iterasi, parameter `max_sideways`
- [ ] Random Restart: jumlah restart, iterasi per restart, parameter `max_restart`
- [ ] SA: plot `e^(ΔE/T)` vs iterasi, frekuensi stuck
- [ ] GA: populasi, iterasi, plot **max & mean** vs iterasi, 2 × 3 variasi × 3 run

### Laporan PDF
- [ ] Cover
- [ ] Deskripsi Persoalan
- [ ] Pembahasan:
  - [ ] Desain: representasi state, objective + penalty (beserta alasannya), neighbor, UB
  - [ ] Penjelasan implementasi tiap algoritma: deskripsi fungsi/kelas + **source code**
  - [ ] Heuristik yang dipakai + sumbernya (delta eval, T0 otomatis, windowing fitness, elitism)
  - [ ] Hasil eksperimen + visualisasi
  - [ ] Analisis (EXPERIMENTS §5)
- [ ] Kesimpulan dan Saran
- [ ] Pembagian tugas
- [ ] Referensi
- [ ] Lampiran **Form Penggunaan Generative AI** (hal. 19 Panduan AI ITB), diisi jujur (lihat §AI Usage Log)
- [ ] Lampiran lainnya (opsional)

---

## Q&A dengan Asisten

Tanya **hanya** lewat komentar di unggahan Tubes di Teams (DM ke asisten tidak dijawab). Cek dulu apakah sudah ada yang nanya.

| # | Pertanyaan | Status | Jawaban |
|---|---|---|---|
| 1 | "Truk / peti kemas / paket" di spec maksudnya kapal / geladak / kendaraan? | open | |
| 2 | Apakah ETA dipakai di objective wajib, atau hanya informasi (boleh dipakai untuk bonus)? | open | |
| 3 | Apakah ada format input / test case resmi dari asisten (misalnya saat demo)? | open | |
| 4 | Boleh pakai objective dengan penalty (state sementara boleh infeasible) asalkan hasil akhir feasible? | open | |
| 5 | Definisi "frekuensi stuck di local optima" pada SA dibebaskan? | open | |
| 6 | `max_sideways`: dihitung berturut-turut atau total? | open | |
| 7 | Bonus 2 "seluruh HC" = Steepest, Stochastic, Sideways, Random Restart saja? | open | |
| 8 | Eksperimen GA: konfigurasi kontrol boleh dipakai bersama di dua set variasi (15 run), atau harus 18 run terpisah? | open | |

## Konvensi Git

- Branch: `feat/<scope>`, `fix/<scope>`, `docs/<scope>`, `exp/<scope>` → PR ke `main` (review minimal 1 anggota lain)
- Commit: `feat(ga): add roulette wheel selection`, `fix(core): overlap count on rotate`, `docs(report): add SA analysis`
- Jangan commit `.venv/`, `__pycache__/`. Output eksperimen final **di-commit** (spec wajib ada `output/`)
