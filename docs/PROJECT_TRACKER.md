# Project Tracker — Tubes 1 IF3070 (G09)

| | |
|---|---|
| **Deadline** | Kamis, 22 Oktober 2026, **22.22 WIB** (release GitHub + submit di Edunex) |
| **Target freeze internal** | Rabu, 21 Oktober 2026 (buffer 1 hari) |
| **Repo** | `IF3070_G09_<NamaKelompok>` (GitHub akun pribadi, **public** sebelum deadline) |
| **Tag release** | `v1.0` (milestone 1, revisi 0). Revisi berikutnya `v1.1`, `v1.2`, … |
| **Demo** | Jadwal menyusul, pantau Teams |

## Anggota

| NIM | Nama | Fokus utama |
|---|---|---|
| | | Core model (state, objective, moves, IO, UB) + Hill-Climbing |
| | | Simulated Annealing + Genetic Algorithm (roulette) |
| | | Visualisasi + experiment runner + koordinator laporan |

Semua anggota menulis bagian laporan untuk algoritma masing-masing dan ikut analisis.

---

## Milestones

### M0 — Setup (25–27 Sep)
- [ ] Isi sheet kelompok (**batas Minggu 27 Sep 23.59**) → dapat nomor kelompok final
- [ ] Rename repo/folder sesuai format `IF3070_GXX_NamaKelompok`, invite anggota
- [ ] Struktur folder: `src/`, `docs/`, `output/`, `README.md`, `.gitignore` (`__pycache__/`, `.venv/`)
- [ ] Baca Q&A di unggahan Teams, lalu kirim pertanyaan terbuka (lihat §Q&A)
- [ ] Tonton ulang / baca salindia Khodra: HC, SA, GA

### M1 — Core Model (28 Sep – 4 Okt)
- [ ] Format input JSON + loader + validasi (DESIGN §2)
- [ ] Generator instance random (seeded) + `src/data/main.json` + 1 instance kecil untuk brute force
- [ ] State + occupancy grid + objective dengan penalty (DESIGN §4)
- [ ] Delta evaluation + 1 self-check (hasil delta = hasil full recompute di ribuan random move)
- [ ] 3 move: move (termasuk ke luar), swap, rotate + random neighbor + full neighborhood
- [ ] Random initial state
- [ ] Upper bound (DP knapsack berat+luas) + brute force instance kecil
- [ ] Visualisasi state: grid deck, kendaraan berwarna + label id, daftar kendaraan di luar, nilai objective/fee/berat

### M2 — Algoritma (5–11 Okt)
- [ ] Steepest Ascent HC
- [ ] SA: T0 otomatis, geometric cooling, catat `e^(ΔE/T)` dan stuck count
- [ ] GA: **roulette wheel selection eksplisit** (cumsum + spin), one-point crossover, mutation, elitism
- [ ] Semua algoritma return format hasil yang sama (EXPERIMENTS §2)
- [ ] CLI: `python src/main.py --algo <hc|sa|ga|...> --instance ... --seed ...`
- [ ] (Bonus 2) Stochastic, Sideways, Random Restart HC

### M3 — Eksperimen (12–16 Okt)
- [ ] Script `experiments.py` untuk menjalankan semua run wajib (24) → `output/`
- [ ] Generate semua plot dari JSON
- [ ] Isi tabel di `EXPERIMENTS.md`
- [ ] Sanity check: semua hasil akhir feasible? durasi masuk akal?

### M4 — Laporan, Bonus, Release (17–21 Okt)
- [ ] Laporan PDF (lihat checklist di bawah)
- [ ] Bonus 1 / 3 kalau waktunya cukup
- [ ] README final (setup, run, pembagian tugas)
- [ ] Repo **public**, tag `v1.0`, buat GitHub Release, submit di Edunex
- [ ] Clone ulang repo di folder bersih, ikuti README dari nol, pastikan jalan

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
