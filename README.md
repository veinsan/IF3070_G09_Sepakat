# CARGO — IF3070_G09_Sepakat

**CARGO (Constraint-Aware Revenue and Geometric Optimization)** adalah kerangka optimasi pemilihan dan penataan kendaraan pada geladak kapal dengan **Hill-Climbing, Simulated Annealing, dan Genetic Algorithm**, untuk Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027.

Program memaksimalkan shipping fee dengan mempertimbangkan posisi integer, orientasi, overlap, batas geladak, dan kapasitas berat. Bonus mencakup objective urgensi ETA, empat varian Hill-Climbing yang disebut dalam spesifikasi, dan armada multi-kapal. Implementasi pencarian hanya memakai standard library Python.

## Struktur

Data, source code, notebook, dokumentasi, dan hasil eksperimen dipisahkan menurut tanggung jawabnya. Karena proyek ini hanya memiliki satu persoalan, tidak ada lapisan `src/local_search/` tambahan.

```text
IF3070_G09_Sepakat/
├── dataset/                         # input JSON: main, small, multi
├── docs/
│   ├── DESIGN.md                    # representasi, objective, algoritma, heuristik
│   ├── EXPERIMENTS.md               # protokol, interpretasi, lokasi hasil
│   ├── PROJECT_TRACKER.md           # status aktual dan checklist pengumpulan
│   └── Spesifikasi ... .md          # dokumen tugas asli, tidak diubah
├── notebooks/
│   └── experiments.ipynb            # analisis dan visualisasi hasil resmi
├── output/
│   ├── experiments/                 # seluruh eksperimen resmi
│   │   ├── hc/steepest/
│   │   ├── sa/sa/
│   │   ├── ga_iter/ga/
│   │   ├── ga_pop/ga/
│   │   ├── hc_variants/{stochastic,sideways,random_restart}/
│   │   ├── eta/sa/
│   │   ├── multi/steepest/
│   │   └── summary*.md, summary*.png
│   ├── analysis/                    # gambar penyajian yang diekspor notebook
│   └── runs/                        # run manual/quick, diabaikan Git
├── src/
│   ├── core/                       # input, generator, state, objective, bounds, ETA
│   ├── search/                     # neighbor, HC, SA, GA, format hasil
│   ├── visualization/              # diagram state dan plot dari hasil tersimpan
│   ├── web/                        # API lokal, worker process, dan frontend statis
│   ├── web_app.py                  # peluncur simulator browser di loopback
│   ├── scripts/build_notebook.py   # sumber notebook yang dapat diregenerasi
│   ├── config.py                   # path dan parameter bersama
│   ├── main.py                     # CLI satu run dan replay
│   └── experiments.py              # runner wajib/bonus dan ringkasan
├── tests/                          # regresi perilaku dengan unittest
├── requirements.txt
└── README.md
```

Laporan PDF belum dibuat. Setelah tersedia, letakkan laporan di `docs/`; status publikasi dan release ada di [tracker](docs/PROJECT_TRACKER.md).

## Setup

Python **3.11+** untuk setup lengkap, CPU; GPU tidak diperlukan. Lingkungan yang diverifikasi memakai Python 3.14.7. Matplotlib dipakai untuk gambar, Notebook/nbclient/nbformat untuk analisis, FastAPI/Uvicorn untuk simulator lokal, dan httpx2 untuk regresi API.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

Seluruh perintah berikut dijalankan dari root repository dengan environment aktif.

## Simulator web lokal

```bash
python src/web_app.py
# Port alternatif jika 8000 sudah digunakan:
python src/web_app.py --port 8767
```

Buka **http://127.0.0.1:8000** (sesuaikan port). Semua aset, termasuk Three.js dan font IBM Plex Sans, disajikan secara lokal; tidak ada CDN, layanan AI eksternal, atau build frontend Node.js.

1. Pilih dataset bawaan atau unggah JSON dengan format yang sama seperti CLI.
2. Pilih algoritma, seed, dan objective. Buka **Parameter algoritma** bila perlu; mengubah formulir tidak otomatis menjalankan search.
3. Klik **Jalankan simulasi**. Search berjalan pada process terpisah; proses dapat dibatalkan.
4. Gunakan **State saat ini / Terbaik feasible**, pemilih kapal, serta **Awal / Sebelumnya / Putar / Berikutnya / Terakhir** untuk mengamati snapshot nyata. Setelah selesai, tampilan mengikuti incumbent feasible jika masih mengikuti snapshot terbaru.
5. Gunakan **2D / 3D** untuk mengganti renderer tanpa menjalankan ulang solver. Dalam 3D, drag untuk orbit, tombol kanan untuk geser, dan scroll untuk zoom. Tombol **Reset / Atas / + / − / Putar kiri / Putar kanan / Fokus pilihan** menyediakan alternatif kontrol kamera; **Layar penuh** memperbesar viewport.
6. Pilih kendaraan lewat geometri SVG/3D, keyboard Tab + Enter pada SVG, atau selector di tab **Inspeksi**. Pemilih kendaraan yang dimuat pada kapal lain juga berpindah ke kapal tersebut. Kendaraan di luar kapal tetap tersedia di daftar, tanpa posisi 3D fiktif.
7. **Bandingkan awal / akhir** menampilkan initial state dan hasil feasible berdampingan dalam 2D; menutupnya mengembalikan mode tampilan sebelumnya. **Grid / Label** mengatur lapisan visual, bukan data pencarian.
8. Lihat kurva dan tabel numerik di bawah viewport. Tab **Hasil** memuat perbandingan sesi serta unduhan JSON atau PNG grafik run, bukan screenshot viewport 3D.

**Batas 3D:** diperlukan WebGL2. Jika inisialisasi grafis gagal atau konteks WebGL terputus, aplikasi kembali ke SVG 2D tanpa membatalkan search atau menghapus hasil. Ukuran/orientasi tapak tetap mengikuti data 2D; tinggi kendaraan, lambung, dan kabin hanya ilustrasi, bukan constraint tambahan. Tidak ada simulasi lintasan berkendara atau penumpukan. Kamera tidak mengikuti perpindahan kendaraan secara otomatis; **Reset** membingkai ulang keadaan terpilih, termasuk posisi di luar batas. Lisensi Three.js dan font tersedia dalam `src/web/static/vendor/three/LICENSE.txt` dan `src/web/static/fonts/OFL.txt`.

**Semantik simulasi:** maksimal 240 snapshot disimpan dengan sampling adaptif; playback tidak merekonstruksi setiap transisi dan tidak menginterpolasi penempatan fiktif. Pada GA, current adalah individu dengan objective maksimum pada generasi tersebut, bukan seluruh populasi. Best feasible adalah arsip terpisah; baseline kapal kosong dinyatakan eksplisit ketika belum ada kandidat feasible yang ditemukan. Pendapatan asli tetap terpisah dari bobot objective ETA.

**Batas lokal:** satu search aktif, deadline 45 detik, dan delapan run terminal terbaru di memori server. Riwayat hilang saat server dihentikan; simpan ekspor yang diperlukan. UI menyingkirkan riwayat yang sudah kedaluwarsa ketika menerima status berikutnya. Batas parameter/input ditampilkan atau divalidasi sebelum worker dimulai; misalnya populasi GA minimal tiga karena elitism dua. Batas demo dapat lebih kecil daripada CLI, termasuk maksimum 2.000 generasi GA.

Run GUI mencakup overhead observasi dan **tidak menggantikan benchmark resmi**. Aplikasi tidak menulis unggahan, hasil search, atau snapshot ke `output/experiments/`. Server hanya menerima akses loopback dan menolak Origin asing; versi ini bukan deployment publik.


## Menjalankan satu algoritma

```bash
python src/main.py --algo hc --seed 1
python src/main.py --algo stochastic --seed 2
python src/main.py --algo sideways --max-sideways 100
python src/main.py --algo random_restart --max-restart 10
python src/main.py --algo sa --iterations 100000 --seed 1
python src/main.py --algo ga --population 100 --iterations 1000 --seed 1
python src/main.py --algo sa --instance multi.json --seed 2
python src/main.py --algo sa --objective eta --seed 1
```

| Opsi | Fungsi |
|---|---|
| `--algo` | `steepest` atau alias `hc`, `stochastic`, `sideways`, `random_restart`, `sa`, `ga` |
| `--instance` | Nama input dalam `dataset/` atau path JSON eksplisit; default `main.json` |
| `--objective` | `fee` atau `eta`; default `fee`, tersedia untuk semua algoritma |
| `--seed` | Seed random, default 1 |
| `--max-sideways`, `--max-restart` | Batas total sideways atau jumlah restart setelah percobaan pertama |
| `--max-no-improve` | Batas proposal tanpa perbaikan pada Stochastic HC |
| `--max-iterations` | Batas pengaman HC; pada Random Restart berlaku per percobaan |
| `--iterations` | Iterasi SA atau generasi GA |
| `--population` | Ukuran populasi GA; harus lebih besar daripada elitism default |
| `--out` | Direktori hasil manual; default `output/runs/` |
| `--no-plot`, `--no-save` | Simpan JSON saja, atau tampilkan hasil tanpa menyimpan |
| `--view JSON` | Buka dan gambar ulang hasil tersimpan, tanpa search |

Parameter lengkap ada di [`src/config.py`](src/config.py). Parameter yang tidak berlaku dan nilai tidak valid ditolak dengan pesan CLI.

Setiap run menghasilkan `<run_id>.json`, `<run_id>_initial.png`, `<run_id>_final.png`, dan `<run_id>_plot.png`. Nama run memakai instance dan seed; GA juga memakai populasi dan generasi. **Run manual dengan identitas yang sama di direktori yang sama mengganti hasil manual sebelumnya.** Default manual tidak menimpa eksperimen resmi.

```bash
python src/main.py --view output/runs/sa/main_seed1.json
# Input eksternal, termasuk hasil objective ETA:
python src/main.py --view path/hasil_eta_seed1.json --instance path/input.json
```

Search boleh melintasi state infeasible. Hasil yang dikembalikan adalah **incumbent feasible terbaik**. Bila budget habis sebelum search mengunjungi state feasible, kapal kosong menjadi baseline yang valid dan status `empty_baseline_used` dicatat eksplisit. Tidak ada repair tersembunyi atau iterasi tambahan; lihat [desain](docs/DESIGN.md).

## Eksperimen resmi

```bash
python src/experiments.py --dry-run
python src/experiments.py
python src/experiments.py --only sa ga_pop
python src/experiments.py --skip-existing
python src/experiments.py --plots-only
python src/experiments.py --quick
```

- **24 run wajib, 39 run dengan bonus.** Kedua sweep GA masing-masing memiliki sembilan pelaksanaan, termasuk kontrol yang diulang secara terpisah.
- Hasil resmi berada di `output/experiments/<grup>/<algoritma>/`; JSON dan gambar berpasangan dengan basename yang sama.
- Mode quick memakai parameter kecil dan, tanpa `--out`, diarahkan ke `output/runs/quick/`.
- `--skip-existing` melewati JSON yang sudah tersedia. Setelah mengubah algoritma, input, atau parameter, jalankan ulang tanpa opsi ini agar tidak memakai hasil lama.
- `summary.md` berisi tabel wajib dan ringkasan. `summary_eta.md` membandingkan fee asli dan urgensi pada seed yang sama.
- `duration_s` mengukur search saja. Pemeriksaan neighborhood untuk metrik stuck SA termasuk durasi dan evaluasi; plotting, serialisasi, dan upper bound pelaporan tidak termasuk.

## Notebook analisis

Notebook CARGO memakai pemisah coklat, banner judul dan kelompok, daftar isi, Pendahuluan, Inisialisasi, narasi sebelum kode, tabel hasil, serta blok Insights. Seluruh angka dan simpulan kuantitatif dihitung dari hasil tersimpan, bukan diketik ulang. Builder dan notebook mandiri; file template tidak diperlukan saat regenerasi maupun eksekusi.

```bash
# Bangun notebook bersih dari sumber Python:
python src/scripts/build_notebook.py
# Bangun, jalankan seluruh sel, dan simpan hasil eksekusi:
python src/scripts/build_notebook.py --execute
# Buka secara interaktif:
jupyter notebook notebooks/experiments.ipynb
```

Jalankan eksperimen resmi lengkap sebelum eksekusi notebook. Notebook memeriksa kelengkapan artefak, menampilkan state awal/akhir, plot HC/SA/GA, dua sweep GA, perbandingan durasi/konsistensi, multi-kapal, ETA, dan optimum eksak instance kecil. Sumbu evaluasi menggunakan hitungan aktual, bukan interpolasi.

Setiap gambar analisis ditanam langsung dalam notebook dan diekspor ke `output/analysis/`. Isi notebook mencakup karakteristik kendaraan, hasil per seed, kurva pencarian, pasangan initial/final state, serta pembahasan keterbatasan. Direktori sumber eksperimen resmi tidak diubah oleh notebook.

**Edit `src/scripts/build_notebook.py`, bukan sel notebook secara manual**, supaya regenerasi tidak menghapus perubahan.

## Generator dan pengujian

```bash
python src/core/generator.py --seed 4 --vehicles 30 --width 10 --length 20 --out output/runs/custom.json
python src/core/generator.py --seed 4 --vehicles 40 --width 10 8 6 --length 12 10 8 --out output/runs/fleet.json
python -m unittest discover -s tests -t .
```

## Pembagian tugas

| NIM | Nama | Tanggung jawab |
|---|---|---|
| 18224061 | Riantama Putra | Input/generator, representasi state, objective dan delta evaluation, neighbor, upper bound, Hill-Climbing, multi-kapal |
| 18224059 | Tiara Kusuma Wardhani | Simulated Annealing, Genetic Algorithm, objective alternatif ETA |
| 18224057 | Levina Nathania Bunardi | Visualisasi, CLI, runner eksperimen, notebook, koordinasi laporan |

Pembagian ini mengikuti dokumen kelompok. Bantuan AI pada sesi perapihan dicatat terpisah dalam tracker dan harus dicantumkan secara jujur dalam formulir laporan.

## Referensi

Spesifikasi asli tersedia di `docs/`. Rujukan algoritma kuliah dan heuristik implementasi dijelaskan pada [`docs/DESIGN.md`](docs/DESIGN.md); protokol serta batas interpretasi hasil ada pada [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md).
