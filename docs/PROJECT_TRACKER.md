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
| **R** | 18224061 | Riantama Putra | Fondasi: setup repo, input/loader + generator instance, core model (state, occupancy, objective + penalty, delta evaluation, moves, UB) + seluruh varian Hill-Climbing + Bonus 3 (multi-kapal) |
| **T** | 18224059 | Tiara Kusuma Wardhani | Simulated Annealing + Genetic Algorithm (roulette) + Bonus 1 (objective ETA) |
| **L** | 18224057 | Levina Nathania Bunardi | Visualisasi + CLI + experiment runner & plot + notebook analisis + koordinator laporan |

Kode `[R]`/`[T]`/`[L]` di milestone = penanggung jawab task. `[All]` = dikerjakan bersama.
Semua anggota menulis bagian laporan untuk algoritma masing-masing dan ikut analisis.

**Fondasi dulu, lalu sesuai pembagian.** Fondasi (branch #1–#6: setup, instance-io, core-state,
neighbors, upper-bound, result-format) dikerjakan `[R]` karena SA, GA, visualisasi, dan runner bergantung ke API
state/objective/move. Setelah fondasi selesai, **setiap anggota hanya mengerjakan task miliknya sendiri**
(tidak mengambil task anggota lain). Kontrak API ada di DESIGN §3–§5.

---

## Jadwal (Sen 19 – Kam 22 Okt)

**Status per Sen 19 pagi:** fondasi #1–#5 selesai dan sudah di `main` (31 unit test lulus). Semua task lain
belum dimulai. Jadwal Jum 16 – Min 18 sebelumnya diganti dengan jadwal di bawah.

Target tetap **semua spek wajib + Bonus 1, 2, 3**. Kolom "Gate" = kondisi yang harus tercapai di akhir hari.

| Hari | R (Riantama) | T (Tiara) | L (Levina) | Gate |
|---|---|---|---|---|
| **Sen 19** | `feat/result-format` (`config.py` + `search/result.py`) **di-merge paling lambat siang**, lalu Steepest HC (`feat/hill-climbing`), lalu mulai varian HC | SA (`feat/simulated-annealing`): T0 otomatis, geometric cooling, history `e^(ΔE/T)`, stuck count | Visualisasi state + plot (`feat/visualization`), input dari dict hasil `search/result.py` | Format hasil ada di `main`; Steepest + SA jalan; state bisa digambar |
| **Sel 20** | Varian HC (Bonus 2) selesai. Bonus 3: generator multi-kapal + instance `multi.json` + test | GA (`feat/genetic-algorithm`): roulette, crossover, mutation, elitism, history max/mean. Bonus 1: objective ETA | CLI `main.py`, `experiments.py`, skeleton notebook, visualisasi multi-kapal | **Code freeze 23.59**: semua algoritma + bonus jalan via CLI |
| **Rab 21** | Tulis bab desain (state, objective, neighbor, UB), HC, dan multi-kapal. Review hasil run HC | Tulis bab SA, GA, dan Bonus 1. Review hasil run SA/GA | Pagi: jalankan semua run (24 wajib + 9 Bonus 2 + 3 Bonus 1 + 3 Bonus 3), plot, isi tabel EXPERIMENTS, notebook. Siang: skeleton laporan, cover, deskripsi persoalan, compile PDF | Sore `[All]`: analisis (EXPERIMENTS §5), kesimpulan & saran, referensi, form AI. **Freeze internal 23.59**: PDF + README final |
| **Kam 22** | Fix minor saja. Repo public, tag `v1.0`, GitHub Release, submit Edunex **≤ 20.00** | Latihan demo | Uji clone bersih dari README, latihan demo | Tersubmit sebelum 22.22 |

- **Sen 19 `[All]`:** kirim pertanyaan Q&A #1–#8 di Teams hari ini. Jawabannya dibutuhkan sebelum laporan
  ditulis Rabu (terutama #5, #6, #8).
- **Kalau gate meleset:** spek wajib tidak boleh mundur. Bonus dipotong dengan urutan **Bonus 1 (3 poin)
  dulu, lalu Bonus 3 (10 poin)**. Bonus 2 (7 poin) dipertahankan karena hanya varian dari Steepest HC.
  Core sudah mendukung banyak kapal (DESIGN §8), jadi sisa Bonus 3 relatif kecil.

---

## Milestones

### M0 — Setup (25–27 Sep) ✅
- [x] Isi sheet kelompok (**batas Minggu 27 Sep 23.59**) → dapat nomor kelompok final (G09)
- [x] Rename repo/folder sesuai format `IF3070_GXX_NamaKelompok`, invite anggota
- [x] Struktur folder: `src/`, `docs/`, `output/`, `README.md`, `.gitignore` (`__pycache__/`, `.venv/`)
- [ ] Baca Q&A di unggahan Teams, lalu kirim pertanyaan terbuka (lihat §Q&A) — **kirim Sen 19**
- [x] Tonton ulang / baca salindia Khodra: HC, SA, GA

### M1 — Core Model (Jum 16 – Min 18 Okt) ✅ (visualisasi pindah ke Sen 19)
- [x] `[R]` Format input JSON + loader + validasi (DESIGN §2)
- [x] `[R]` Generator instance random (seeded) + `src/data/main.json` + 1 instance kecil untuk brute force
- [x] `[R]` State + occupancy grid + objective dengan penalty (DESIGN §4)
- [x] `[R]` Delta evaluation + 1 self-check (hasil delta = hasil full recompute di ribuan random move)
- [x] `[R]` 3 move: move (termasuk ke luar), swap, rotate + random neighbor + full neighborhood
- [x] `[R]` Random initial state
- [x] `[R]` Upper bound (DP knapsack berat+luas) + brute force instance kecil
- [ ] `[L]` Visualisasi state: grid deck, kendaraan berwarna + label id, daftar kendaraan di luar, nilai objective/fee/berat

### M2 — Algoritma (Sen 19 – Sel 20 Okt)
- [x] `[R]` Steepest Ascent HC
- [x] `[T]` SA: T0 otomatis, geometric cooling, catat `e^(ΔE/T)` dan stuck count
- [x] `[T]` GA: **roulette wheel selection eksplisit** (cumsum + spin), one-point crossover, mutation, elitism
- [x] `[R]` `config.py` + `search/result.py`: format hasil seragam (EXPERIMENTS §2), dipakai semua algoritma
- [ ] `[L]` CLI: `python src/main.py --algo <hc|sa|ga|...> --instance ... --seed ...`
- [x] `[R]` (Bonus 2) Stochastic, Sideways, Random Restart HC

### M3 — Eksperimen (Sel 20 – Rab 21 Okt)
- [ ] `[L]` Script `experiments.py` untuk menjalankan semua run wajib (24) + Bonus 2 (9) + Bonus 1 (3) + Bonus 3 (3) → `output/`
- [ ] `[L]` Generate semua plot dari JSON
- [ ] `[All]` Isi tabel di `EXPERIMENTS.md` (masing-masing untuk algoritmanya)
- [ ] `[All]` Sanity check: semua hasil akhir feasible? durasi masuk akal?

### M4 — Laporan, Bonus, Release (Sel 20 – Kam 22 Okt)
- [ ] `[L]` Laporan PDF (koordinator; isi per bab oleh pemilik bagian, lihat checklist di bawah)
- [x] `[T]` Bonus 1 (objective ETA, 3 run)
- [x] `[R]` Bonus 3: generator multi-kapal + instance `multi.json` + test (state, neighbor, UB sudah mendukung banyak kapal)
- [ ] `[L]` Bonus 3: visualisasi multi-kapal (`final_state.decks` berisi grid tiap kapal)
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
- [x] Simulated Annealing
- [x] Genetic Algorithm dengan **roulette wheel selection**
- [ ] State menampilkan: kendaraan di dalam & di luar, keadaan geladak, value
- [ ] Visualisasi initial state, final state, dan hasil eksperimen

### Data per run (lihat EXPERIMENTS.md)
- [ ] Semua algoritma: state awal & akhir, objective akhir, plot objective vs iterasi, durasi
- [ ] Steepest / Stochastic HC: jumlah iterasi
- [ ] Sideways: jumlah iterasi, parameter `max_sideways`
- [ ] Random Restart: jumlah restart, iterasi per restart, parameter `max_restart`
- [x] SA: plot `e^(ΔE/T)` vs iterasi, frekuensi stuck
- [x] GA: populasi, iterasi, plot **max & mean** vs iterasi, 2 × 3 variasi × 3 run

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
| 1 | "Peti kemas / paket" di spec maksudnya geladak / kendaraan? | open | "Truk" → "kapal" sudah dikoreksi di spec v1.1 (07/10/2026) |
| 2 | Apakah ETA dipakai di objective wajib, atau hanya informasi (boleh dipakai untuk bonus)? | open | |
| 3 | Apakah ada format input / test case resmi dari asisten (misalnya saat demo)? | open | |
| 4 | Boleh pakai objective dengan penalty (state sementara boleh infeasible) asalkan hasil akhir feasible? | open | |
| 5 | Definisi "frekuensi stuck di local optima" pada SA dibebaskan? | open | |
| 6 | `max_sideways`: dihitung berturut-turut atau total? | open | Dipakai: **total**, langsung berhenti saat tercapai (paling literal dengan kalimat spek, DESIGN §7.1) |
| 7 | Bonus 2 "seluruh HC" = Steepest, Stochastic, Sideways, Random Restart saja? | open | Dipakai: keempatnya (sesuai varian yang disebut di bagian Cakupan spek) |
| 8 | Eksperimen GA: konfigurasi kontrol boleh dipakai bersama di dua set variasi (15 run), atau harus 18 run terpisah? | open | |

## Konvensi Git

- Branch: `feat/<scope>`, `fix/<scope>`, `docs/<scope>`, `exp/<scope>`, `chore/<scope>` → PR ke `main` (review minimal 1 anggota lain)
- Branch dibuat dari `main` terbaru **saat fitur mulai dikerjakan**, bukan semuanya di awal, supaya tidak basi
  dan tidak konflik. Satu branch = satu fitur = satu PR.
- Commit: `feat(ga): add roulette wheel selection`, `fix(core): overlap count on rotate`, `docs(report): add SA analysis`
- Jangan commit `.venv/`, `__pycache__/`. Output eksperimen final **di-commit** (spec wajib ada `output/`)

### Rencana Branch (urutan merge)

| # | Branch | Isi | PJ | Status |
|---|---|---|---|---|
| 1 | `chore/project-setup` | Struktur repo, `requirements.txt`, README, konvensi kode (DESIGN §10) | R | ✅ |
| 2 | `feat/instance-io` | `core/problem.py`, `core/generator.py`, `data/main.json`, `data/small.json` | R | ✅ |
| 3 | `feat/core-state` | `core/state.py`, `core/objective.py` + test delta = full recompute | R | ✅ |
| 4 | `feat/neighbors` | `search/neighbors.py` + test | R | ✅ |
| 5 | `feat/upper-bound` | `core/bounds.py` (DP knapsack + brute force) | R | ✅ |
| 6 | `feat/result-format` | `config.py`, `search/result.py` (format hasil seragam, EXPERIMENTS §2) | R | ✅ |
| 7 | `feat/hill-climbing` | Steepest Ascent | R | ✅ |
| 8 | `feat/visualization` | `visualization/state_view.py`, `visualization/plots.py` | L | Sen 19 |
| 9 | `feat/simulated-annealing` | `search/simulated_annealing.py` | T | ✅ |
| 10 | `feat/hc-variants` | Stochastic, Sideways, Random Restart (Bonus 2) | R | ✅ |
| 11 | `feat/genetic-algorithm` | `search/genetic_algorithm.py` (roulette) | T | ✅ |
| 12 | `feat/cli` | `main.py` | L | Sel 20 |
| 13 | `feat/multi-ship` | Generator multi-kapal + `multi.json` + test (Bonus 3) | R | ✅ |
| 13b | `feat/visualization` (lanjutan) | Visualisasi multi-kapal (Bonus 3) | L | Sel 20 |
| 14 | `feat/eta-objective` | Objective ETA (Bonus 1): `core/eta_objective.py`, `eta_experiments.py` | T | ✅ |
| 15 | `exp/main-experiments` | `experiments.py`, `output/`, `notebooks/experiments.ipynb` | L | Sel 20 – Rab 21 |
| 16 | `docs/report` | Laporan PDF + README final | L | Rab 21 |
