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

- [x] Builder `src/scripts/build_notebook.py` mengikuti `ref/notebook/`, dengan banner, daftar isi, Introduction, Initialization, dan Insights.
- [x] Analisis kualitas, durasi, konsistensi, dua sweep GA, HC/SA, ETA, multi-kapal, UB dan optimum eksak disusun dari hasil aktual.
- [x] Sumbu konvergensi memakai evaluasi kumulatif aktual, bukan interpolasi.
- [x] Regresi penuh: `python -m unittest discover -s tests -t .` lulus dengan 156 test.
- [x] Smoke CLI default HC/SA/GA; singleton; budget pendek; ETA initial; ekspor bertitik; replay ETA; dan penolakan parameter invalid dijalankan.
- [x] Evaluasi independen seluruh 39 JSON beserta pemetaan, history, feasibility, dan pasangan PNG berhasil.
- [x] Notebook dieksekusi ulang: 63 sel (19 sel kode), 26 gambar PNG tertanam, tanpa error sel.

Hasil eksekusi notebook yang disimpan merupakan bagian artefak analisis. Regenerasi harus dilakukan melalui builder; pemeriksaan output gambar merupakan bagian verifikasi visual, bukan hanya memeriksa exit code.

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

Skill notebook berasal dari `ref/notebook/` yang diberikan pengguna. Rujukan nbclient dipakai untuk API eksekusi notebook.

Riwayat penggunaan AI sebelum sesi ini tidak diketahui assistant. Setiap anggota perlu mencatat penggunaan aktualnya sendiri ketika mengisi formulir laporan; log ini tidak menggantikan formulir resmi dan tidak mengklaim kode sepenuhnya ditulis tanpa bantuan AI.
