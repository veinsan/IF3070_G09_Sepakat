# Project Tracker — G09 Sepakat

Status ini mengikuti implementasi dan artefak aktual, bukan jadwal lama. Fokus sesi perapihan adalah kode, organisasi repository, eksperimen, dan notebook. **PDF laporan serta publikasi/pengumpulan tetap terpisah.**

## Kelompok dan pengumpulan

| Item | Keterangan |
|---|---|
| Repository | [veinsan/IF3070_G09_Sepakat](https://github.com/veinsan/IF3070_G09_Sepakat) |
| Anggota | Riantama Putra (18224061), Tiara Kusuma Wardhani (18224059), Levina Nathania Bunardi (18224057) |
| Deadline spesifikasi | 22 Oktober 2026, 22.22 WIB |
| Format release | `vX.Y`; rencana milestone pertama `v1.0` |
| Status remote terakhir yang diperiksa | PRIVATE, belum ada tag atau GitHub Release; tidak diubah pada sesi ini |
| Demo | Jadwal mengikuti pengumuman resmi; kesiapan demo tidak dianggap sudah diverifikasi untuk seluruh anggota |

Pembagian tugas anggota dipertahankan pada README. Kontribusi AI pada sesi ini dicatat di bagian akhir, tidak disamarkan sebagai pekerjaan mandiri anggota.

## Implementasi wajib

- [x] Source local search dalam Python; modul search/core hanya memakai standard library.
- [x] Loader/validasi JSON, generator seeded, dan input utama/kecil/armada dalam `dataset/`.
- [x] Representasi seluruh kendaraan di dalam/luar, posisi integer, orientasi, dan grid setiap geladak.
- [x] Initial state random dengan RNG lokal.
- [x] Move, swap dalam/luar/lintas kapal, dan rotate; input satu kendaraan tidak gagal pada swap.
- [x] Objective shipping fee, penalty overlap/batas/kapasitas, evaluasi penuh dan delta evaluation.
- [x] Final state feasible pada budget kecil maupun penuh; baseline kosong diungkapkan bila belum ada kandidat feasible yang dikunjungi.
- [x] Steepest Ascent, Stochastic, Sideways Move, dan Random Restart HC.
- [x] SA, pendinginan, peluang penerimaan, checkpoint local optimum terkonfirmasi, serta stagnasi terpisah.
- [x] GA dengan roulette eksplisit, crossover satu titik, mutasi, elitism, dan history max/mean.
- [x] CLI semua algoritma serta objective fee/ETA; replay hasil termasuk path input eksplisit.
- [x] Penamaan hasil mempertahankan nama instance bertitik dan seed yang berbeda.
- [x] Sumber materi algoritma dalam komentar modul; heuristik dan referensi dijelaskan dalam DESIGN.

## Bonus

- [x] Objective alternatif ETA tanpa atribut persoalan baru; pendapatan asli tidak dilabeli sebagai bobot urgensi.
- [x] Empat varian HC yang disebut pada bagian Cakupan spesifikasi.
- [x] Multi-kapal: input, constraint per kapal, move/swap lintas kapal, total value, dan visualisasi semua geladak.

## Eksperimen dan organisasi

- [x] Dua sweep GA masing-masing sembilan pelaksanaan; kontrol tidak dipakai bersama sebagai satu eksekusi.
- [x] Tiga seed untuk HC, SA, tiap varian HC, ETA, dan multi-kapal.
- [x] Total 24 run wajib dan 39 run termasuk bonus, dihasilkan ulang dari implementasi sekarang.
- [x] Semua hasil resmi feasible dan tidak memakai baseline kosong; objective/field turunan dihitung ulang dari state.
- [x] State awal/akhir, objective, parameter, durasi, iterasi, dan evaluasi tersimpan.
- [x] Restart/iterasi per restart, batas sideways, peluang SA/stuck, serta max/mean GA tercatat.
- [x] JSON/gambar terpisah per grup di `output/experiments/`; run manual/quick tidak menimpa hasil resmi secara default.
- [x] Gambar initial/final/plot setiap run serta tiga gambar ringkasan tersedia.
- [x] Output flat versi lama dihapus setelah hasil pengganti tervalidasi.
- [x] README, DESIGN, dan EXPERIMENTS diperbarui; tabel hasil hanya memiliki sumber resmi di output, bukan salinan markdown yang mudah basi.

## Notebook dan verifikasi

- [x] Builder notebook CARGO mandiri, dengan banner coklat, daftar isi, Pendahuluan, Inisialisasi, narasi sebelum kode, dan blok Insights.
- [x] Analisis kualitas, durasi, konsistensi, dua sweep GA, HC/SA, ETA, multi-kapal, UB dan optimum eksak disusun dari hasil aktual.
- [x] Sumbu konvergensi memakai evaluasi kumulatif aktual, bukan interpolasi.
- [x] Regresi penuh terkini: `python -m unittest discover -s tests -t .` lulus dengan 167 test, termasuk observer dan API lokal; `pip check` tidak menemukan dependency rusak.
- [x] Smoke CLI default HC/SA/GA; singleton; budget pendek; ETA initial; ekspor bertitik; replay ETA; dan penolakan parameter invalid dijalankan.
- [x] Evaluasi independen seluruh 39 JSON beserta pemetaan, history, feasibility, dan pasangan PNG berhasil.
- [x] Notebook CARGO dieksekusi ulang: 119 sel (25 sel kode), 28 gambar PNG tertanam, dan 16 tabel HTML, tanpa error sel.
- [x] Builder dan seluruh sel berhasil dieksekusi pada salinan proyek tanpa file template; 28 figure analisis diekspor ke `output/analysis/`.
- [x] Render HTML diperiksa di browser: warna border coklat, tautan daftar isi, tabel, plot GA, dan pasangan state; seluruh 28 gambar termuat dan memiliki alternative text.
- [x] Checksum seluruh 39 JSON eksperimen resmi identik sebelum dan sesudah eksekusi notebook.

Hasil eksekusi notebook yang disimpan merupakan bagian artefak analisis. Regenerasi harus dilakukan melalui builder; pemeriksaan output gambar merupakan bagian verifikasi visual, bukan hanya memeriksa exit code.

## Simulator web lokal

- [x] FastAPI/Uvicorn menyajikan frontend native dan solver Python pada satu alamat loopback; tanpa deployment cloud, database, atau build Node.js.
- [x] Observer pada enam algoritma mempertahankan history, final state, metadata pencarian, dan evaluasi; regresi juga mencakup ETA dan budget nol.
- [x] Snapshot posisi terpisah dari state mutable, dibatasi 240 frame, dan dapat diputar tanpa membuat penempatan interpolasi.
- [x] Konfigurasi/upload JSON, SVG kapal, current/best feasible, inspeksi keyboard/selector, perbandingan awal/akhir, grafik, tabel numerik, dan perbandingan sesi berfungsi.
- [x] Worker terpisah menjaga HTTP responsif; satu run aktif, pembatalan, deadline, cleanup shutdown, batas input/DP, Origin/Host lokal, dan retensi hasil diverifikasi.
- [x] Smoke HTTP menjalankan keenam algoritma, multi-kapal, ETA, dan ekspor JSON/PNG. Browser juga menjalankan SA utama 100.000 iterasi dan GA utama 1.000 generasi.
- [x] History, final state, dan evaluasi SA utama dengan observer identik dengan hasil resmi pada seed yang sama.
- [x] Browser memverifikasi keyboard pada SVG, playback, pembatalan, pemilih kapal, unduhan nyata, pemulihan ekspor kedaluwarsa, dan reduced motion.
- [x] Layout 375/768/1440 px tidak menambah horizontal page overflow. Kontras teks tombol utama 6,78:1 dan batas input 3,56:1 terukur; font disajikan lokal.
- [x] Checksum 171 berkas yang dilindungi, termasuk artefak eksperimen, notebook, template pengguna, dan `.gitignore`, tidak berubah.

### Workbench 2D/3D

- [x] Viewport dominan, panel kanan Konfigurasi/Inspeksi/Hasil, serta dock replay dan grafik; identitas coklat dan font lokal dipertahankan.
- [x] Three.js 0.186.1 lokal berlisensi MIT, kapal/kendaraan prosedural, kamera orbit/atas/zoom/fokus/fullscreen, grid/label, dan picking.
- [x] Tapak dan rotasi model berasal dari snapshot aktual; tidak ada constraint tinggi, stacking, lintasan berkendara, atau posisi fiktif kendaraan luar.
- [x] Seleksi, current/best, kapal, replay, dan perbandingan 2D tersinkronisasi; shader/renderer tidak mengganti keputusan solver.
- [x] Bug canvas nol setelah keluar dari comparison dan bug framing saat aspect ratio menyempit direproduksi lalu diperbaiki; layout 375/768/812/1440 px diverifikasi tanpa horizontal page overflow.
- [x] Inersia kamera mengikuti reduced motion. Toggle berulang mempertahankan satu canvas dan alokasi scene yang diamati; render idle teramati nol.
- [x] WebGL tidak tersedia dan kehilangan konteks dipaksakan; fallback SVG tetap mempertahankan hasil, solver, serta ekspor JSON/PNG.
- [x] SA utama, GA utama, multi-kapal/ETA, kamera, seleksi pointer/native, keyboard tab, replay, fullscreen, dan unduhan nyata dijalankan; 167 regresi Python lulus.
- [x] Checksum 241 berkas yang dilindungi tetap sama; algoritma/backend, artefak resmi, notebook, materi pengguna, dan `.gitignore` tidak diubah.

Catatan verifikasi: Chromium headless tetap melaporkan dokumen visible saat fokus dipindah. Handler visibility tersedia, tetapi suspend melalui perpindahan tab native belum terbukti pada lingkungan pengujian ini; tidak ada klaim FPS.


## Pekerjaan laporan — belum dikerjakan pada sesi ini

- [ ] PDF dalam `docs/`, meliputi cover dan deskripsi persoalan.
- [ ] Pembahasan implementasi fungsi/kelas beserta source code, heuristik, hasil, visualisasi, dan analisis.
- [ ] Kesimpulan dan saran.
- [ ] Pembagian tugas dan referensi pada PDF.
- [ ] Lampiran Form Penggunaan Generative AI, diisi jujur sesuai panduan resmi.
- [ ] Review bersama dan ekspor PDF final.

## Pekerjaan publikasi dan demo — belum dijalankan

- [ ] Review perubahan, commit kontribusi secara jujur, dan push versi final.
- [ ] Ubah repository menjadi public sebelum pengumpulan.
- [ ] Buat tag/release dengan format spesifikasi setelah PDF tersedia.
- [ ] Submit tautan/deliverables pada Edunex sebelum deadline.
- [ ] Isi jadwal demo, latihan skenario, dan pastikan semua anggota memahami implementasi.

Tidak ada commit, push, perubahan visibility, tag, release, atau submit yang dilakukan oleh assistant pada sesi perapihan ini.

## Interpretasi spesifikasi dan Q&A

Tidak ada jawaban asisten Teams yang diasumsikan telah diperoleh. Implementasi mengambil keputusan berikut secara eksplisit:

| Topik | Keputusan implementasi |
|---|---|
| Istilah paket/peti kemas | Diartikan kendaraan/geladak sesuai konteks persoalan kapal |
| ETA | Tidak mengubah objective wajib; dipakai pada bonus objective alternatif |
| State infeasible sementara | Dipakai untuk eksplorasi dengan penalty; hasil akhir selalu dipilih feasible |
| Frekuensi stuck SA | Episode local optimum terkonfirmasi pada checkpoint berkala; stagnasi dicatat terpisah |
| Maximum sideways | Total sepanjang run dan berhenti saat batas tercapai |
| Seluruh HC | Empat varian yang disebut di bagian Cakupan; Stochastic memakai proposal random/rejection sebagaimana didokumentasikan |
| Dua sweep GA | Dilaksanakan terpisah, sehingga tidak membutuhkan izin reuse kontrol |
| Input saat demo | Format JSON yang didokumentasikan; belum ada test case asisten lain yang diasumsikan kompatibel |

Keputusan di atas bukan kutipan jawaban resmi. Pertanyaan administratif atau perbedaan interpretasi salindia tetap disampaikan melalui kanal Teams yang ditetapkan, bukan DM asisten.

## Log penggunaan AI pada sesi perapihan

Assistant membantu audit spesifikasi dan kode, identifikasi/reproduksi bug, modifikasi core/search/CLI/runner/visualisasi, reorganisasi dataset/output, penulisan regresi, pembuatan ulang notebook dan analisis, pembaruan dokumentasi, serta eksekusi verifikasi dan eksperimen. Hasil review dan pemeriksaan runtime digunakan untuk memperbaiki implementasi; ini bukan audit yang hanya memberi saran.

Penyajian notebook mengikuti template visual yang diberikan pengguna. File template bukan dependensi runtime maupun regenerasi; rujukan nbclient dipakai untuk API eksekusi notebook.

Pada sesi simulator lokal, AI membantu merancang kontrak UI/API, mengimplementasikan observer, worker/backend dan frontend, menambahkan regresi perilaku, memperbaiki masalah upload/parameter/retensi/fokus SVG/overflow yang ditemukan saat verifikasi, serta menjalankan smoke HTTP dan browser. Tidak ada eksperimen resmi yang diganti atau klaim hasil baru yang dimasukkan ke notebook.

Pada sesi workbench 3D, AI membantu merancang ulang shell antarmuka, membuat renderer prosedural Three.js, mengintegrasikan kontrol dan pemilihan snapshot, memverifikasi dependency berlisensi, memperbaiki transisi comparison/framing/reduced motion, serta menjalankan smoke WebGL dan regresi. Geometri dekoratif bukan perluasan model optimasi. Inspirasi komposisi antarmuka dan asal dependency dicatat pada `DESIGN.md`; tidak ada kode algoritma atau hasil eksperimen resmi yang diganti.

Riwayat penggunaan AI sebelum sesi ini tidak diketahui assistant. Setiap anggota perlu mencatat penggunaan aktualnya sendiri ketika mengisi formulir laporan; log ini tidak menggantikan formulir resmi dan tidak mengklaim kode sepenuhnya ditulis tanpa bantuan AI.
