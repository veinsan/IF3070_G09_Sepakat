# CARGO — Desain Optimasi Muatan Kendaraan

Dokumen ini menjelaskan implementasi yang berjalan, bukan rencana fitur. Spesifikasi tugas asli di direktori ini tidak diubah. Source code merupakan sumber detail fungsi/kelas; hasil terukur berada di `output/experiments/` dan notebook.

## 1. Persoalan dan input

Setiap kendaraan mempunyai id, dimensi integer, shipping fee, berat, dan ETA. Setiap kapal mempunyai id, dimensi geladak integer, dan kapasitas berat. Pilihan solusi adalah seluruh kendaraan di luar kapal atau menempatkannya pada satu geladak dengan posisi dan orientasi tertentu.

Input JSON dalam `dataset/` memakai `ships` dan `vehicles`. Banyak kapal diterima melalui list `ships`; tidak ada format single-ship terpisah. Loader menolak id kosong/duplikat, dimensi bukan integer positif, berat/kapasitas tidak positif, fee negatif, ETA bukan integer nonnegatif, dan angka non-finite. Metadata generator diabaikan oleh loader.

Contoh input minimal yang dapat dimuat:

```json
{
  "ships": [
    {"id": "Deck-1", "width": 10, "length": 20, "max_capacity": 500}
  ],
  "vehicles": [
    {"id": "A", "width": 3, "length": 4, "shipping_fee": 60, "weight": 5, "eta": 3}
  ]
}
```

| Input | Pemakaian |
|---|---|
| `main.json` | Instance utama bersama untuk eksperimen wajib dan varian HC |
| `small.json` | Smoke run dan pembuktian optimum eksak dengan brute force |
| `multi.json` | Bonus armada tiga kapal dengan ukuran dan kapasitas berbeda |

Generator menggunakan katalog dimensi kendaraan, fee/berat acak, dan ETA acak. Seed dan parameter pembentukan dicatat pada `meta`. Kapasitas tiap kapal diturunkan dari luas geladak dan berat rata-rata per sel, sehingga kapasitas maupun geometri dapat menjadi pembatas.

## 2. Representasi state

```python
positions[i] = None                     # seluruh kendaraan di luar kapal
positions[i] = (ship_index, x, y, 'H')   # anchor kiri atas
positions[i] = (ship_index, x, y, 'V')
```

`H` menempati width kolom dan length baris; `V` menukar kedua dimensi. Anchor random berada di dalam geladak, tetapi badan kendaraan pada state pencarian sementara boleh melewati batas dan menerima penalty. Koordinat integer.

Initial state tetap random: tiap kendaraan masuk dengan peluang `INITIAL_P_INSIDE`, kemudian kapal, anchor, dan orientasinya dipilih acak. Tidak ada penataan greedy berdasarkan fee. Setiap fungsi menerima RNG lokal dari seed; tidak memakai RNG global.

`State` menyimpan occupancy per sel/per kapal, overlap, sel keluar batas, fee, dan berat per kapal. `to_dict()` menghasilkan semua kendaraan di dalam/luar dan semua grid geladak. Grid memakai string kosong untuk sel kosong dan gabungan id untuk overlap; visualisasi menampilkan pelanggaran secara eksplisit.

Initial state eksplisit pada API harus cocok dengan isi problem. State disalin agar algoritma tidak mengubah objek pemanggil. Wrapper ETA mengikat ulang posisi initial ke problem dengan objective transformasi.

## 3. Objective dan constraint

Untuk objective wajib:

```text
f(s) = total_fee - P * (overlap_cells + out_of_bound_cells + weight_units)
P = max(shipping_fee) + 1
weight_units = jumlah per kapal ceil(excess_weight / min_vehicle_weight)
```

- `overlap_cells` menjumlahkan occupancy berlebih, bukan hanya jumlah pasangan kendaraan.
- `out_of_bound_cells` menjumlahkan bagian kendaraan yang melewati geladak.
- Kapasitas dan occupancy dipisahkan per kapal; kendaraan di kapal berbeda tidak overlap.
- Berat dibandingkan dengan toleransi numerik `EPS`. Pelanggaran positif di luar toleransi tetap mendapat minimal satu unit penalty.

Karena fee satu kendaraan lebih kecil daripada `P`, mengeluarkan kendaraan yang menyebabkan pelanggaran memberi langkah perbaikan. Konsekuensinya, HC dengan neighborhood lengkap yang benar-benar berhenti di local optimum tidak berhenti pada state infeasible. **Argumen ini tidak berlaku jika budget iterasi memotong pencarian sebelum local optimum.**

### Incumbent feasible

Semua algoritma mempertahankan arsip `FeasibleIncumbent`, terpisah dari state berjalan atau maksimum objective penalized populasi. Arsip dimulai dari kapal kosong bernilai nol: penempatan ini valid karena spesifikasi membolehkan semua kendaraan tidak diangkut.

Setiap state feasible yang benar-benar dikunjungi diperiksa terhadap arsip. `final_state` adalah incumbent feasible terbaik; jika tidak ada state feasible yang dikunjungi, hasilnya tetap baseline kosong. Ini bukan repair setelah search: tidak ada kendaraan yang dihapus diam-diam atau iterasi tambahan.

| Field | Makna |
|---|---|
| `extra.empty_baseline_used` | Belum ada state feasible yang dikunjungi; hasil memakai baseline kosong |
| `extra.found_feasible` | Search mengunjungi setidaknya satu state feasible |
| `extra.raw_final_objective`, `raw_final_is_feasible` | Endpoint mentah search/populasi, sebelum pemilihan incumbent |
| `extra.raw_best_objective` | Objective penalized terbaik yang terlihat, tidak harus feasible |
| `history.best_feasible` | Nilai incumbent feasible per iterasi/generasi |

Baseline tidak boleh ditafsirkan sebagai keberhasilan optimasi. Final state valid tidak berarti optimal. Plot mempertahankan history mentah dan menambahkan incumbent jika nilainya berbeda.

### Delta evaluation

`State.delta(changes)` menerapkan lalu membatalkan perubahan pada satu atau dua kendaraan. Hanya occupancy yang tersentuh yang diperbarui; tidak membangun ulang seluruh grid. Evaluator penuh `core.objective.evaluate` menjadi pembanding independen untuk pengujian dan laporan akhir. Penyalinan state, serialisasi, serta evaluasi untuk pelaporan bukan iterasi search tambahan.

## 4. Neighborhood

| Operasi | Definisi |
|---|---|
| Move | Pindah kendaraan ke anchor/orientasi lain, ke luar kapal, atau masuk dari luar |
| Swap | Tukar anchor dan kapal dua kendaraan; pertahankan orientasi sendiri jika sudah berada di dalam |
| Rotate | Tukar H/V pada anchor yang sama untuk kendaraan nonpersegi di dalam kapal |

Kendaraan yang masuk melalui swap dari luar memakai orientasi pasangan karena representasi luar tidak memiliki orientasi. Swap dua kendaraan yang sama-sama di luar tidak mengubah state. Bila hanya ada satu kendaraan, random neighbor tidak mencoba memilih pasangan swap kosong.

HC Steepest/Sideways memakai enumerasi neighborhood. SA, Stochastic HC, dan mutasi GA memakai proposal random: tipe move dipilih acak, lalu parameternya diacak. Untuk kendaraan di dalam, target keluar dan target koordinat random diberi peluang sama. Heuristik ini mencegah peluang removal menjadi sangat kecil ketika jumlah koordinat besar.

## 5. Hill-Climbing

| Varian | Aturan | Penghentian |
|---|---|---|
| Steepest Ascent | Evaluasi semua neighbor, pilih delta terbesar; tie-break acak dengan reservoir sampling | Tidak ada delta positif, atau batas pengaman |
| Stochastic | Proposal satu neighbor random; terima hanya jika membaik | `max_no_improve` proposal tanpa perbaikan berturut-turut, atau batas iterasi |
| Sideways Move | Neighbor terbaik; boleh delta nol | Local optimum ketat, total sideways mencapai `max_sideways`, atau batas iterasi |
| Random Restart | Steepest dari initial random, kemudian initial random baru | `max_restart` restart selesai; total percobaan = restart + 1 |

Implementasi Stochastic memakai sampling proposal/rejection, bukan enumerasi seluruh improving neighbor atau pembobotan proporsional besar delta. Penghentiannya adalah batas sampling, bukan bukti local optimum.

Satu iterasi Steepest/Sideways adalah satu perpindahan; satu iterasi Stochastic adalah satu proposal. Pada Random Restart, perpindahan ke initial baru dihitung sebagai satu langkah pada history gabungan. `iters_per_restart` dan stop reason tiap percobaan tetap dicatat. Sideways dihitung total sepanjang run, sesuai pembacaan literal batas maksimum pada spesifikasi.

## 6. Simulated Annealing

Move dengan delta nonnegatif diterima; move yang memperburuk diterima dengan peluang `exp(delta/T)`. T0 dihitung dari sampel random neighbor yang memperburuk agar penurunan rata-rata awal mempunyai peluang penerimaan `SA_T0_ACCEPT`. Jika tidak ada sampel buruk, T0 bernilai 1. Ini heuristik turunan persamaan peluang, bukan jaminan penerimaan semua move buruk sebesar nilai tersebut.

Pendinginan geometris memakai `alpha = (T_min / T0) ** (1 / N)`. Bila T0 sudah tidak lebih besar daripada T_min, suhu tidak dinaikkan. Jumlah iterasi default tetap sesuai konfigurasi. Peluang untuk delta negatif disimpan sebagai pasangan iterasi/nilai; move nonnegatif diterima dengan peluang satu dan tidak dimasukkan ke scatter tersebut.

### Stuck dan stagnasi berbeda

Setiap `stuck_window` iterasi, neighborhood current diperiksa sampai ditemukan delta positif atau seluruh neighbor habis. Checkpoint adalah local optimum hanya jika tidak ada neighbor membaik. `stuck_count` menghitung episode rangkaian checkpoint local-optimum: dihitung pada checkpoint pertama, kemudian baru dapat dihitung lagi setelah checkpoint non-local-optimum.

Ini **frekuensi episode yang teramati secara berkala**, bukan klaim mendeteksi setiap kunjungan singkat. `history.local_optimum` merekam observasi. `stagnation_count` terpisah menghitung window tanpa raw-best baru; tidak disebut sebagai jumlah local optimum.

Seluruh probe konfirmasi termasuk `evaluations` dan `duration_s`, sehingga SA tidak tampak lebih murah dengan menyembunyikan biaya monitoring. Pemeriksaan tidak mengonsumsi RNG dan tidak mengubah lintasan SA.

## 7. Genetic Algorithm

Chromosome adalah list posisi kendaraan yang sama dengan state HC/SA. Populasi awal random. Fitness roulette memakai windowing `fit_i = f_i - min(f) + epsilon` agar positif. Cumulative sum dibentuk per generasi; spin dilakukan eksplisit dengan pencarian biner.

Crossover satu titik menghasilkan dua anak tanpa memutasi induk. Mutasi diterapkan per anak dengan peluang tetap, menggunakan satu random neighbor. Elitism membawa individu terbaik sesuai objective penalized. Skor elit dipakai ulang; anak dinilai setelah crossover/mutasi. Arsip feasible memeriksa seluruh populasi, bukan hanya individu raw-max.

`history.objective` adalah maksimum populasi dan `history.mean` adalah rata-rata populasi per generasi. `best_generation` menunjukkan generasi incumbent feasible, atau `None` jika baseline; `raw_best_generation` terpisah. Crossover koordinat dapat menimbulkan overlap meskipun induk feasible; ini alasan penalty dan perbedaan max/mean perlu dibahas.

Dua sweep resmi masing-masing dijalankan tiga kali per konfigurasi, tanpa deduplikasi kontrol. Parameter lain tetap. Pengulangan kontrol pada seed yang sama tetap deterministik dan tidak boleh dianggap sebagai enam sampel independen pada ringkasan kualitas antaralgoritma.

## 8. Upper bound dan bonus

`upper_bound` adalah relaksasi knapsack luas dan berat gabungan; geometri penempatan dan pembagian muatan per kapal diabaikan. Kendaraan yang tidak dapat muat pada kapal mana pun dikeluarkan. Pembulatan berat/kapasitas memperhitungkan toleransi agar relaksasi tidak lebih ketat daripada feasibility evaluator.

`gap_ub = (UB - objective) / UB` pada hasil feasible merupakan batas atas gap relatif terhadap optimum; bukan jarak pasti. `brute_force` menggunakan backtracking, bitmask sel, dan branch-and-bound untuk optimum eksak instance kecil. Jika mencapai batas node, fungsi gagal eksplisit, bukan mengklaim optimum.

Bonus ETA menggunakan `fee * (1 + 1/(eta + 1))`, tanpa atribut persoalan baru. Problem turunan mengganti nilai yang dioptimasi, sedangkan fee asli dicatat pada `extra.shipping_fee_total`. `total_fee` pada JSON ETA masih berarti jumlah bobot transformasi; CLI/gambar memberi label bobot urgensi dan fee asli secara terpisah. UB ETA memakai objective yang sama.

Bonus multi-kapal memakai constraint per kapal, move/swap lintas kapal, dan objective total armada. Semua algoritma memakai API state yang sama. Visualisasi menggambar semua geladak dan kendaraan di luar armada.

## 9. Organisasi dan sumber

`core/` mengelola model; `search/` mengelola algoritma; `visualization/` menggambar hasil tersimpan. CLI satu run dan runner eksperimen terpisah. Data berada di `dataset/`, notebook di `notebooks/`, builder di `src/scripts/`, dan hasil resmi terpisah dari percobaan manual.

Notebook CARGO menggunakan builder mandiri dengan pemisah bagian berwarna coklat, tabel HTML, dan figure PNG tertanam. Figure analisis juga diekspor ke `output/analysis/`; hasil JSON resmi tetap hanya dibaca. File template visual tidak dibutuhkan untuk menjalankan maupun meregenerasi notebook.

- M. L. Khodra, [Hill-Climbing Search](https://www.youtube.com/watch?v=L0b0CN3Fds8), 2021.
- M. L. Khodra, [Simulated Annealing](https://www.youtube.com/watch?v=AdhG7HnhYrk), 2021.
- M. L. Khodra, [Genetic Algorithm](https://www.youtube.com/watch?v=aI41TGo9J9c), 2021.
- [NBClient](https://nbclient.readthedocs.io/en/latest/client.html): eksekusi notebook terprogram.

Penalty, baseline feasible, pemilihan T0, bias proposal removal, tie-breaking, windowing, elitism, relaksasi UB, dan observasi checkpoint adalah keputusan implementasi yang harus dijelaskan kembali pada laporan, bukan diatribusikan otomatis seluruhnya kepada salindia.

## 10. Simulator lokal

`web_app.py` menjalankan satu aplikasi FastAPI/Uvicorn di `127.0.0.1`; `web/server.py` menangani validasi, job, dan ekspor, `web/worker.py` menjalankan search pada process terpisah, dan `web/static/` memuat HTML/CSS/JavaScript serta aset lokal. Frontend native menyediakan SVG sebagai acuan 2D dan Three.js sebagai renderer 3D opsional, tanpa framework frontend atau layanan eksternal.

Keenam algoritma menerima observer opsional tanpa mengubah keputusan pencarian, RNG, history, atau hitungan evaluasi. Tanpa observer, CLI dan runner resmi tidak membuat snapshot. `search/trace.py` menyimpan paling banyak 240 snapshot dengan penjarangan adaptif, mempertahankan langkah awal/akhir, dan menyalin posisi agar frame lama tidak berubah. Pembaruan antarprocess dibatasi frekuensinya; event akhir membawa hasil dan trace lengkap.

Frame memisahkan current dan incumbent feasible. Pada GA, current adalah individu raw-max pada generasi tersebut, sedangkan statistik maksimum/rata-rata populasi tetap berasal dari history algoritma. Posisi dapat tidak feasible selama pencarian; SVG menunjukkan overlap/keluar batas dan UI menampilkan pelanggaran kapasitas. Fee asli dihitung dari input asli, bukan bobot transformasi ETA.

Backend memvalidasi JSON memakai parser core yang sama, lalu membatasi ukuran input, geometri, kapasitas, pekerjaan DP, dan parameter sebelum memulai worker. Hanya satu job aktif, dengan deadline 45 detik dan delapan hasil terminal terakhir di memori. Pembatalan, timeout, dan shutdown menghentikan worker; metadata retensi membuat UI mengenali hasil yang sudah kedaluwarsa. Ini aplikasi loopback, bukan layanan publik.

UI menyediakan playback sampling, inspeksi kendaraan lewat pointer/keyboard/selector, multi-kapal, perbandingan awal/akhir, history numerik terpaginasikan, perbandingan sesi, dan unduhan JSON/PNG. Kurva panjang diringkas dengan mempertahankan ekstrem tiap kelompok; history lengkap tetap tersedia. Observer dan rendering tidak dipakai untuk mengganti durasi benchmark resmi. Tidak ada hasil GUI yang otomatis ditulis ke artefak eksperimen.

Workbench menempatkan viewport sebagai area utama, kontrol/inspeksi/hasil pada panel kanan bertab, serta timeline dan grafik pada dock bawah. `app.js` mempertahankan satu sumber pemilihan run, frame, current/best, kapal, dan kendaraan untuk kedua renderer. Mode visual dan kamera tidak mengubah seed, posisi, objective, atau algoritma. Perbandingan awal/akhir memakai dua SVG dan mengembalikan pilihan 3D ketika ditutup.

`scene3d.js` membangun model kapal/kendaraan low-poly prosedural. Koordinat grid x/y dipetakan ke bidang X/Z; orientasi V menukar lebar/panjang tapak dan memutar model 90°. Tinggi model bersifat ilustratif. Kendaraan yang tidak dimuat tidak diberi posisi fiktif, sedangkan overlap dan posisi keluar batas ditandai tanpa memperbaiki snapshot. Dek optimasi tetap berupa persegi panjang yang ditandai; lambung/kabin dekoratif tidak memperluas area yang diizinkan.

Renderer dimuat secara lazy, menggunakan satu konteks WebGL2 dengan DPR maksimum 1,5, dan memakai ulang objek/geometri antarframe. Render diminta saat ada pembaruan atau perubahan kamera/ukuran, serta selama damping menyelesaikan gerakan; tidak ada loop render idle. Reduced motion menonaktifkan inersia kamera. Listener, RAF, geometri, material, tekstur, dan kontrol dibersihkan saat disposal. Kegagalan inisialisasi/konteks grafis mengembalikan UI ke SVG, bukan mengganti hasil solver. Kamera mempertahankan pose selama replay; Reset/Atas membingkai ulang, dan perubahan aspect ratio mempertahankan lebar serta tinggi bidang pandang yang diperlukan.

Regresi membandingkan observer aktif/nonaktif pada semua algoritma dan objective ETA. Smoke browser menguji jalur interaksi nyata, layout 375/768/1440 px, reduced motion, dan ekspor. Pencarian SA utama 100.000 iterasi dengan observer juga dibandingkan dengan history dan final state resmi.

Smoke workbench 3D menjalankan SA utama 100.000 iterasi dan GA utama 1.000 generasi dengan hasil nyata; transformasi model H/V dicocokkan terhadap posisi snapshot. Kamera, picking vs drag, selector lintas kapal, objective ETA, perbandingan 2D, replay, fullscreen, reduced motion, serta unduhan JSON/PNG juga dijalankan. Regresi Python berjumlah 167 dan lulus dengan `python -m unittest discover -s tests -t .`. Transisi perbandingan → 3D → layar 375 px serta framing pada 375/768/812/1440 px diverifikasi setelah perbaikan; tidak ada horizontal page overflow. Delapan siklus toggle memakai canvas yang sama dan mempertahankan alokasi teramati 10 geometri/10 tekstur pada scene yang diuji; keadaan idle teramati tanpa callback render. Angka tersebut bukan benchmark FPS atau jaminan performa semua perangkat. Pengujian dilakukan di Chromium headless; pergantian fokus tab tetap melaporkan dokumen visible, sehingga suspend melalui visibility native belum terverifikasi pada lingkungan ini.

Grafis diuji dengan penolakan pembuatan konteks dan kehilangan konteks WebGL yang disengaja. Fallback mempertahankan run, frame, objective, serta ekspor; ini bukan fallback data sintetis. Checksum 241 berkas core/search/backend, tes, data/hasil, notebook, materi pengguna, dan `.gitignore` tetap identik.

Rujukan antarmuka: [FastAPI static files](https://fastapi.tiangolo.com/tutorial/static-files/), [lifespan](https://fastapi.tiangolo.com/advanced/events/), serta [Starlette TestClient](https://www.starlette.io/testclient/). IBM Plex Sans didistribusikan lokal dengan lisensi pada `src/web/static/fonts/OFL.txt`; pengambilan font hanya dilakukan saat pengembangan, bukan ketika aplikasi dijalankan.

Komposisi viewport/panel/dock mengambil inspirasi visual dari [Ember Scope](https://github.com/JesseQin123/ember-scope); kode scene dan model kapal/kendaraan dibuat untuk persoalan CARGO, bukan memakai terrain atau simulasi kebakarannya. Three.js **0.186.1** beserta `OrbitControls` berasal dari [paket npm resmi](https://registry.npmjs.org/three/-/three-0.186.1.tgz), disalin tanpa modifikasi ke `src/web/static/vendor/three/` bersama lisensi MIT. Import map lokal menghubungkan `three.module.js`, `three.core.js`, dan addon versi yang sama. Integritas tarball diverifikasi sebelum penyalinan: `sha512-blFeqb49wRCSGUGj7gtpfnSGHy2lwDk94RhUmS1c/hTby70kvChbWpkJ4Pm1390LqzzvTmzgXKHPEafJwCb8jA==`. Pengambilan dependency hanya saat pengembangan; mode 2D tidak mengunduh modul 3D saat startup.

