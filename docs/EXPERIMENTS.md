# Protokol dan Analisis Eksperimen

Dokumen ini menyimpan protokol dan batas interpretasi. **Tabel hasil lengkap tidak diduplikasi di sini**: sumbernya adalah JSON resmi dan [`output/experiments/summary.md`](../output/experiments/summary.md). Analisis kuantitatif, gambar, dan simpulan yang dihitung ulang tersedia pada [`notebooks/experiments.ipynb`](../notebooks/experiments.ipynb).

## 1. Instance dan kontrol

- Eksperimen wajib dan varian HC memakai `dataset/main.json` yang sama.
- Bonus multi-kapal memakai `dataset/multi.json`.
- `dataset/small.json` dipakai untuk smoke run serta optimum eksak, bukan dicampur ke tabel perbandingan utama.
- Seed default setiap konfigurasi adalah 1, 2, dan 3.
- Seluruh parameter ada di `src/config.py` dan ikut disimpan dalam setiap hasil JSON.
- Pengacakan memakai RNG lokal. Penempatan initial HC/SA dengan seed yang sama identik; GA memiliki populasi random dan menyimpan individu awal terbaik sebagai initial state representatif.

| Grup | Algoritma/konfigurasi | Jumlah pelaksanaan |
|---|---|---:|
| `hc` | Steepest Ascent | 3 |
| `sa` | Simulated Annealing | 3 |
| `ga_iter` | Populasi 100; generasi 300, 1000, 3000 | 9 |
| `ga_pop` | Generasi 1000; populasi 50, 100, 200 | 9 |
| `hc_variants` | Stochastic, Sideways, Random Restart | 9 |
| `eta` | SA, objective urgensi ETA | 3 |
| `multi` | Steepest Ascent pada armada | 3 |
| **Total** | **Wajib 24; termasuk bonus** | **39** |

Konfigurasi kontrol GA dilaksanakan secara terpisah di kedua sweep dan disimpan pada direktori berbeda. Ini mengikuti pembacaan konservatif permintaan dua sweep. Karena seed/parameter identik, keluaran kontrol deterministik bukan enam sampel kualitas independen. Ringkasan antaralgoritma memakai satu set tiga seed per konfigurasi.

## 2. Menjalankan dan menyimpan

```bash
python src/experiments.py --dry-run
python src/experiments.py
python src/experiments.py --only hc sa
python src/experiments.py --skip-existing
python src/experiments.py --plots-only
python src/experiments.py --quick
```

Hasil resmi: `output/experiments/<grup>/<algoritma>/<run_id>.json`. Gambar initial/final/plot berdampingan dengan JSON. Ringkasan serta gambar perbandingan berada di akar `output/experiments/`. Run manual memakai `output/runs/`; quick tanpa `--out` memakai `output/runs/quick/`.

`--skip-existing` hanya melanjutkan kumpulan hasil yang sudah ada. Setelah kode, data, atau parameter berubah, jalankan ulang tanpa opsi tersebut. Jangan mencampur hasil versi lama dan baru untuk analisis.

Versi sebelum perapihan menyimpan kontrol GA bersama, memakai definisi stagnasi sebagai stuck, dan memiliki kondisi mesin berbeda untuk ETA. Artefak lama digantikan oleh regenerasi lengkap; angka lama tidak dipertahankan sebagai hasil resmi versi sekarang.

## 3. Kontrak data per run

| Field | Isi |
|---|---|
| `initial_state`, `final_state` | Semua kendaraan di dalam/luar dan grid semua geladak |
| `initial_objective`, `final_objective` | Nilai state awal dan incumbent feasible akhir |
| `is_feasible`, `violations` | Feasibility dan rincian overlap, keluar batas, kelebihan berat |
| `total_fee` | Pendapatan pada objective fee; jumlah bobot pada objective ETA |
| `extra.shipping_fee_total` | Pendapatan asli kendaraan yang dimuat pada run ETA |
| `used_weight`, `capacity`, `used_area_pct`, `loaded` | Utilisasi muatan |
| `upper_bound`, `gap_ub` | Relaksasi dan gap terhadap UB objective yang dioptimasi |
| `duration_s` | Durasi search saja, tanpa IO, plotting, dan UB pelaporan |
| `iterations`, `evaluations` | Banyak langkah/generasi dan pekerjaan evaluasi aktual |
| `history.objective` | Current objective; pada GA maksimum populasi |
| `history.mean` | Rata-rata objective populasi GA |
| `history.best_feasible` | Incumbent feasible per langkah, termasuk baseline kosong |
| `history.evaluations` | Evaluasi kumulatif aktual untuk sumbu konvergensi |
| `history.prob` | SA: pasangan iterasi dan peluang menerima penurunan |
| `history.local_optimum` | SA: hasil konfirmasi neighborhood pada checkpoint |
| `extra` | Restart, sideways, stuck/stagnasi, raw endpoint, baseline, serta mesin search |

Initial state random boleh infeasible. Final state harus feasible, tetapi dapat berupa baseline kosong jika budget belum menemukan kandidat valid. Status ini dicatat dan tidak diperlakukan sebagai keberhasilan pencarian.

## 4. Iterasi, evaluasi, dan durasi

- Steepest/Sideways: satu iterasi adalah satu perpindahan; scan terakhir tanpa perbaikan termasuk evaluasi, bukan perpindahan.
- Stochastic: satu iterasi adalah satu proposal neighbor, termasuk yang ditolak.
- Random Restart: history percobaan disambung, termasuk satu langkah perpindahan initial per restart; iterasi tiap percobaan juga dicatat terpisah.
- SA: satu iterasi adalah satu proposal. Sampling T0 dan konfirmasi local optimum menambah evaluasi, bukan iterasi.
- GA: satu iterasi adalah satu generasi. Evaluasi menghitung populasi awal dan anak baru; skor elit dipakai ulang.

`history.evaluations` memakai hitungan aktual, bukan asumsi biaya merata antariterasi. Jumlah evaluasi tetap bukan unit biaya identik: satu delta probe tidak sama biayanya dengan penilaian/crossover individu. Durasi diperlukan bersama hitungan tersebut.

SA memeriksa local optimum setiap `stuck_window` iterasi. `stuck_count` menghitung episode checkpoint yang terkonfirmasi tidak mempunyai neighbor lebih baik; `stagnation_count` menghitung window tanpa raw-best baru. Kunjungan di antara checkpoint dapat tidak terdeteksi. Biaya monitoring tidak disembunyikan dari durasi SA.

Mesin search dicatat pada `extra.machine` dan ringkasan. Regenerasi seluruh run dilakukan pada lingkungan yang sama, secara berurutan. Pengulangan notebook hanya memproses hasil; tidak boleh menghasilkan durasi search baru atau mengganti provenance mesin run.

## 5. Analisis yang disediakan notebook

Notebook membahas seluruh pertanyaan analisis spesifikasi:

1. **Kedekatan ke optimum:** gap terhadap UB pada instance utama, serta optimum eksak pada instance kecil. UB tidak disamakan dengan optimum geometris.
2. **Perbandingan kualitas:** best, mean, serta incumbent akhir tiap algoritma pada instance yang sama.
3. **Durasi:** mean waktu dan jumlah evaluasi, dengan perbedaan biaya iterasi/monitoring dijelaskan.
4. **Konsistensi:** simpangan baku/range pada tiga seed; tidak mengklaim signifikansi statistik dari sampel kecil.
5. **Budget GA:** dua sweep terpisah, nilai maksimum/rata-rata populasi, dan perubahan kualitas terhadap populasi/generasi.
6. **HC:** plateau/sideways, kualitas versus biaya restart, serta batas sampling Stochastic.
7. **SA:** probabilitas penerimaan penurunan, checkpoint local optimum, dan perbedaannya dari stagnasi.
8. **Bonus:** pemakaian tiap kapal dan perbandingan bobot urgensi, pendapatan asli, serta ETA kendaraan dimuat.

Insight kuantitatif dibentuk dari JSON saat eksekusi, bukan angka yang ditanam pada markdown. Dugaan penyebab seperti crossover merusak susunan dibedakan dari pengukuran langsung. Tanpa ablasi, tidak disimpulkan bahwa satu heuristik merupakan penyebab tunggal hasil.

## 6. Batas interpretasi

- Tiga seed memenuhi minimum tugas, tetapi tidak membuktikan dominasi statistik atau generalisasi ke semua instance.
- Konfigurasi GA dengan mean tertinggi dipilih berdasarkan data eksperimen yang sama; ini perbandingan deskriptif, bukan evaluasi hold-out.
- Penambahan generasi/populasi juga menambah budget komputasi; kenaikan kualitas tidak otomatis menunjukkan efisiensi yang lebih baik.
- ETA adalah objective berbeda. Bandingkan kedua penempatan menggunakan pendapatan asli dan bobot yang sama, bukan langsung menyamakan nilai objective mentah.
- `final_state` adalah incumbent feasible, bukan selalu state current terakhir atau raw-max populasi. Plot menyatakan perbedaannya.
- Perubahan jumlah evaluasi dan durasi SA dibanding versi lama dipengaruhi konfirmasi neighborhood yang baru; jangan menggabungkan tabel lama dan baru.

## 7. Artefak untuk laporan

- [Tabel semua run dan ringkasan](../output/experiments/summary.md).
- [Perbandingan objective fee dan ETA](../output/experiments/summary_eta.md).
- [Notebook analisis dan visualisasi](../notebooks/experiments.ipynb).
- [Penjelasan desain dan referensi](DESIGN.md).

Gambar wajib sudah dipisahkan per grup/algoritma; pilih initial/final/plot yang sesuai ketika menyusun laporan. PDF dan formulir penggunaan AI tetap pekerjaan pengumpulan yang terpisah dari eksekusi eksperimen.
