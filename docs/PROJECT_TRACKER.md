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

## Jadwal Ulang (Jum 16 – Kam 22 Okt)

Target: **semua spek wajib + Bonus 1, 2, 3 selesai**. Kolom "Gate" = kondisi yang harus tercapai di akhir
hari. Kalau gate meleset, yang wajib didahulukan. Bonus boleh geser ke Senin/Selasa, tapi **tidak boleh
makan Rabu** (hari laporan).

| Hari | R (Riantama) | T (Tiara) | L (Levina) | Gate |
|---|---|---|---|---|
| **Jum 16** | Kontrak API (signature state/objective/move) di pagi hari, lalu state + occupancy + objective + delta eval + self-check, 3 move, random init | Review salindia SA/GA, tulis SA & GA terhadap kontrak API (pakai stub dulu) | Loader + validasi, generator instance, `main.json` + instance kecil | Core API jalan, `main.json` ada |
| **Sab 17** | UB (DP knapsack) + brute force, Steepest HC | SA selesai: T0 otomatis, cooling, history `e^(ΔE/T)`, stuck count | Visualisasi state + writer result JSON (EXPERIMENTS §2) | HC & SA run end-to-end + bisa divisualisasi |
| **Min 18** | Bonus 2: Stochastic, Sideways, Random Restart HC | GA selesai: roulette, crossover, mutation, elitism, history max/mean | CLI `main.py` + `experiments.py` + fungsi plot | **Code freeze spek wajib**, semua algoritma jalan via CLI |
| **Sen 19** | Bonus 3: multi-kapal di core (constraint per kapal, move/swap lintas kapal, UB total) | Bonus 1: objective ETA, dibuat sebagai bobot per kendaraan supaya delta eval tidak berubah | Jalankan 24 run wajib + 9 run Bonus 2, generate plot, isi tabel EXPERIMENTS. Skeleton laporan + cover + deskripsi persoalan | Semua hasil wajib + Bonus 2 ada di `output/` |
| **Sel 20** | Bonus 3 selesai + 3 run, tulis bab core + HC | 3 run Bonus 1, tulis bab SA + GA | Visualisasi multi-kapal, plot ringkasan (box plot, overlay konvergensi), tulis bab eksperimen | Semua run bonus selesai, draf laporan per bab |
| **Rab 21** | `[All]` analisis (EXPERIMENTS §5), kesimpulan & saran, referensi, form AI | `[All]` (sama) | Compile PDF, README final, uji clone bersih | **Freeze internal 23.59**: PDF + README final |
| **Kam 22** | Fix minor saja. Repo public, tag `v1.0`, GitHub Release, submit Edunex **≤ 20.00** | Latihan demo | Latihan demo | Tersubmit sebelum 22.22 |

---

## Milestones

### M0 — Setup (25–27 Sep) ✅
- [x] Isi sheet kelompok (**batas Minggu 27 Sep 23.59**) → dapat nomor kelompok final (G09)
- [x] Rename repo/folder sesuai format `IF3070_GXX_NamaKelompok`, invite anggota
- [x] Struktur folder: `src/`, `docs/`, `output/`, `README.md`, `.gitignore` (`__pycache__/`, `.venv/`)
- [ ] Baca Q&A di unggahan Teams, lalu kirim pertanyaan terbuka (lihat §Q&A) — ditunda
- [x] Tonton ulang / baca salindia Khodra: HC, SA, GA

### M1 — Core Model (Jum 16 – Sab 17 Okt)
- [ ] `[L]` Format input JSON + loader + validasi (DESIGN §2)
- [ ] `[L]` Generator instance random (seeded) + `src/data/main.json` + 1 instance kecil untuk brute force
- [ ] `[R]` State + occupancy grid + objective dengan penalty (DESIGN §4)
- [ ] `[R]` Delta evaluation + 1 self-check (hasil delta = hasil full recompute di ribuan random move)
- [ ] `[R]` 3 move: move (termasuk ke luar), swap, rotate + random neighbor + full neighborhood
- [ ] `[R]` Random initial state
- [ ] `[R]` Upper bound (DP knapsack berat+luas) + brute force instance kecil
- [ ] `[L]` Visualisasi state: grid deck, kendaraan berwarna + label id, daftar kendaraan di luar, nilai objective/fee/berat

### M2 — Algoritma (Sab 17 – Min 18 Okt)
- [ ] `[R]` Steepest Ascent HC
- [ ] `[T]` SA: T0 otomatis, geometric cooling, catat `e^(ΔE/T)` dan stuck count
- [ ] `[T]` GA: **roulette wheel selection eksplisit** (cumsum + spin), one-point crossover, mutation, elitism
- [ ] `[All]` Semua algoritma return format hasil yang sama (EXPERIMENTS §2)
- [ ] `[L]` CLI: `python src/main.py --algo <hc|sa|ga|...> --instance ... --seed ...`
- [ ] `[R]` (Bonus 2) Stochastic, Sideways, Random Restart HC

### M3 — Eksperimen (Sen 19 – Sel 20 Okt)
- [ ] `[L]` Script `experiments.py` untuk menjalankan semua run wajib (24) + Bonus 2 (9) → `output/`
- [ ] `[L]` Generate semua plot dari JSON
- [ ] `[All]` Isi tabel di `EXPERIMENTS.md` (masing-masing untuk algoritmanya)
- [ ] `[All]` Sanity check: semua hasil akhir feasible? durasi masuk akal?

### M4 — Laporan, Bonus, Release (Sen 19 – Kam 22 Okt)
- [ ] `[L]` Laporan PDF (koordinator; isi per bab oleh pemilik bagian, lihat checklist di bawah)
- [ ] `[T]` Bonus 1 (objective ETA, 3 run)
- [ ] `[R]` Bonus 3 (multi-kapal di core, 3 run) + `[L]` visualisasi multi-kapal
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

- Branch: `feat/<scope>`, `fix/<scope>`, `docs/<scope>`, `exp/<scope>`, `chore/<scope>` → PR ke `main` (review minimal 1 anggota lain)
- Branch dibuat dari `main` terbaru **saat fitur mulai dikerjakan**, bukan semuanya di awal, supaya tidak basi
  dan tidak konflik. Satu branch = satu fitur = satu PR.
- Commit: `feat(ga): add roulette wheel selection`, `fix(core): overlap count on rotate`, `docs(report): add SA analysis`
- Jangan commit `.venv/`, `__pycache__/`. Output eksperimen final **di-commit** (spec wajib ada `output/`)

### Rencana Branch (urutan merge)

| # | Branch | Isi | PJ |
|---|---|---|---|
| 1 | `chore/project-setup` | Struktur repo, `requirements.txt`, README, konvensi kode (DESIGN §10) | R |
| 2 | `feat/instance-io` | `core/problem.py`, `core/generator.py`, `data/main.json`, `data/small.json` | L |
| 3 | `feat/core-state` | `core/state.py`, `core/objective.py` + test delta = full recompute | R |
| 4 | `feat/neighbors` | `search/neighbors.py` + test | R |
| 5 | `feat/upper-bound` | `core/bounds.py` (DP knapsack + brute force) | R |
| 6 | `feat/visualization` | `visualization/state_view.py`, `visualization/plots.py` | L |
| 7 | `feat/hill-climbing` | `config.py`, `search/result.py`, Steepest Ascent | R |
| 8 | `feat/simulated-annealing` | `search/simulated_annealing.py` | T |
| 9 | `feat/genetic-algorithm` | `search/genetic_algorithm.py` (roulette) | T |
| 10 | `feat/cli` | `main.py` | L |
| 11 | `feat/hc-variants` | Stochastic, Sideways, Random Restart (Bonus 2) | R |
| 12 | `exp/main-experiments` | `experiments.py`, `output/`, `notebooks/experiments.ipynb` | L |
| 13 | `feat/eta-objective` | Objective ETA (Bonus 1) | T |
| 14 | `feat/multi-ship` | Multi-kapal di core + visualisasi (Bonus 3) | R, L |
| 15 | `docs/report` | Laporan PDF + README final | L |
