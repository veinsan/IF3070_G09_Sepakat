![](data:image/png;base64...)

**Tugas Besar 1**

**IF3070 Dasar Inteligensi Artifisial 2026/2027**

**Dosen Pengampu:** Ir. Windy Gambetta, MBA

Dr. Nur Ulfa Maulidevi, S.T, M.Sc.

*Dipersiapkan oleh Tim Asisten Laboratorium Inteligensi Artifisial 2023*

*Versi: 1.1 07/10/2026*

*Sistem pengerjaan:* ***Take Home Berkelompok***

*Deadline pengumpulan:* ***Kamis, 22 Oktober 2026 Pukul 22.22 WIB****.*

#

# Log Perubahan Dokumen

| **Versi** | **Tanggal** | **Perubahan** |
| --- | --- | --- |
| 1.0 | 24/09/2026 | Rilis awal. |
| 1.1 | 07/10/2026 | Mengganti kata “Truk” menjadi “Kapal”. |

#

# Daftar Isi

[**Log Perubahan Dokumen 2**](#_3emtbthcihrx)

[**Daftar Isi 3**](#_t1ck1gmfsbiz)

[**Tujuan 4**](#_l7j7ttultpd9)

[**Aturan 5**](#_zho0g95vb8pb)

[**Deliverables 6**](#_ju7r8843lxeu)

[**Timeline 7**](#_2o1atpg9bgxn)

[**Deskripsi 8**](#_ltnq8p4n3p7i)

[**Spesifikasi 9**](#_jzbuyjnknq2l)

[Daftar Variabel Permasalahan 9](#_674f8ahs1374)

[Ketentuan Representasi 10](#_16kfomfwyzlo)

[Objective Function & Constraints 10](#_804ys6nzotzz)

[**Cakupan 11**](#_8e4w8thmqgs2)

[**Bonus 14**](#_uosgwrx1ju04)

[**Referensi 15**](#_95ykveyv1yhf)

[**Salam dari Asisten 16**](#_563k1k4v4u62)

#

# Tujuan

Tugas Besar I pada kuliah IF3070 Dasar Intelegensi Buatan bertujuan agar peserta kuliah mendapatkan wawasan tentang bagaimana cara mengimplementasikan dan mengevaluasi algoritma-algoritma *local search* untuk menyelesaikan permasalahan berupa studi kasus yang relevan terhadap industri.

Pada tugas ini peserta akan merancang representasi solusi, mengimplementasikan beberapa varian algoritma *local search*, melakukan eksperimen, dan menganalisis hasilnya.

#

# Aturan

Terdapat beberapa hal yang perlu diperhatikan dalam pengerjaan tugas ini:

1. Tugas besar dilaksanakan **secara berkelompok**. Pembagian kelompok ditentukan sendiri oleh mahasiswa dengan mengisi sheet kelompok [berikut ini](https://docs.google.com/spreadsheets/d/1lLPUCyTkPeWsxs6qZHCHwmyv3m3D3Zl7KeI2gpfIscY/edit?usp=sharing) dengan 1 kelompok terdiri dari **3 mahasiswa** yang dapat berasal dari lintas kelas. Batas waktu pengisian kelompok adalah **Minggu, 27 September 2026 pukul 23.59 WIB**. Silakan lihat instruksi lebih lanjut di *sheets* kelompok di atas.
2. **Utamakan implementasi yang mengacu pada salindia kuliah**. Apabila menggunakan atau mengadaptasi metode dari sumber di Internet, **sumber tersebut wajib dicantumkan** dalam bentuk komentar pada program serta referensinya pada laporan.
3. Jika terdapat hal yang kurang dipahami, peserta dapat mengajukan pertanyaan kepada asisten melalui **komentar pada Unggahan Tugas Besar di Teams**. Pertanyaan yang diajukan secara personal kepada asisten tidak akan dijawab untuk menghindari perbedaan informasi yang diterima.
4. Dilarang melakukan plagiarisme, meminta atau memberikan kode dan/atau laporan kepada kelompok lain, dan alasan **penggunaan LLM tidak dapat diterima**. Pelanggaran terhadap aturan ini akan mengakibatkan **pemberian nilai E** kepada seluruh anggota kelompok yang terlibat.

# *Deliverables*

Berikut *deliverables* dalam pengerjaan tugas ini:

1. Untuk tugas ini, setiap kelompok diwajibkan menggunakan *version control system* Git dengan membuat *repository* pada GitHub (akun pribadi). Format penamaan *repository* adalah **IF3070\_GXX\_NamaKelompok**, dengan XX merupakan nomor kelompok yang terdapat pada [sheet kelompok](https://docs.google.com/spreadsheets/d/1lLPUCyTkPeWsxs6qZHCHwmyv3m3D3Zl7KeI2gpfIscY/edit?usp=sharing). *Repository* dapat bersifat *private* selama masa pengerjaan dan **wajib diubah menjadi *public*** sebelum pengumpulan agar dapat diakses oleh asisten.
2. Meskipun *commit* dan *development* tidak dinilai secara langsung, setiap kelompok diharapkan melakukan *commit* dan *branching* yang mengikuti *best practice*. Disarankan menggunakan [*semantic commit*](https://gist.github.com/joshbuchea/6f47e86d2510bce28f8e7f42ae84c716) agar kontribusi tiap anggota dapat terlihat dengan jelas.
3. *Repository* harus memiliki struktur sebagai berikut:

* Folder **src**, digunakan untuk menyimpan *source code*.
* Folder **docs,** digunakan untuk menyimpan laporan dalam bentuk **.pdf** yang terdiri atas komponen berikut:
  + **Cover**
  + **Deskripsi Persoalan**
  + **Pembahasan** yang berisi penjelasan implementasi algoritma *local search* (berisi deskripsi fungsi/kelas beserta *source code*), hasil dan analisis eksperimen (disertai dengan visualisasi dari program yang telah dibuat)
  + **Kesimpulan dan Saran**
  + **Pembagian tugas** tiap anggota kelompok
  + **Referensi**
  + **Lampiran Form Penggunaan Generative AI** yang diisi dengan sejujur-jujurnya(Halaman 19 pada [Panduan AI ITB](https://drive.google.com/file/d/1sKEun1xTuK5UW8ktrkuZtVTU-1YRE-_n/view?usp=sharing)). Apabila terdapat indikasi kecurangan atau ketidakjujuran, maka akan **ditindaklanjuti sesuai hukum yang berlaku**.
  + **Lampiran Lainnya** (bila ada)
* Folder **output**, digunakan untuk menyimpan hasil *run* algoritma.
* **README.md**, yang berisi deskripsi singkat *repository*, cara *setup* dan *run program*, dan pembagian tugas tiap anggota kelompok.

1. Pengumpulan dilakukan dengan membuat *release* dengan *tag* **vX.Y** pada *repository* yang telah dibuat sebelum *deadline*, dengan **X adalah nomor *milestone*** dan **Y adalah angka revisi** yang dimulai dari 0 untuk versi awal. Pastikan format *tag* sesuai ketentuan. Pengumpulan yang melewati *deadline* akan dikenakan **pengurangan nilai**.

# *Timeline*

#

| **No** | **Waktu** | **Kegiatan** |
| --- | --- | --- |
| 1 | Kamis, 24 September 2026 | Rilis Tugas Besar I IF3070. |
| 2 | Minggu, 27 September 2026 | Batas pengisian daftar kelompok. |
| 3 | Kamis, 22 Oktober 2026 | Pengumpulan *final deliverables* tugas besar pada platform Edunex. |
| 4 | [Menyusul] | Batas pengisian jadwal demo tugas besar. |
| 5 | [Menyusul] | Pelaksanaan demo tugas besar. |

#

# Deskripsi

![](data:image/png;base64...)

Gambar 1. 1 (Sumber: [Gambar Kapal](https://www.supplychainbrain.com/articles/38645-dnv-approves-worlds-largest-green-car-carrier-design))

Anda adalah seorang *Forward Deployed Engineer* (FDE) di PT ~~Owen~~ Intim Line yang mengoperasikan kapal kargo pengangkut kendaraan. Perusahaan baru saja memperoleh kontrak pengiriman dari beberapa dealer kendaraan sekaligus. Pada setiap jadwal keberangkatan, perusahaan menerima daftar kendaraan dengan dimensi, berat, tarif pengiriman, dan deadline yang berbeda-beda.

Selama ini, penempatan kendaraan pada geladak kapal dilakukan secara manual. Akibatnya, ruang geladak sering tidak termanfaatkan dengan baik dan keputusan pemilihan letak kendaraan belum tentu menghasilkan keuntungan yang optimal.

Tim operasional meminta Anda membangun sistem pendukung keputusan untuk menentukan kendaraan yang akan diangkut serta posisi dan orientasi setiap kendaraan pada geladak. Sistem tersebut harus dapat mengevaluasi berbagai kemungkinan konfigurasi, mempertimbangkan fungsi-fungsi objektif yang ditentukan, dan menghasilkan solusi penataan yang optimal.

#

# Spesifikasi

Tugas ini bertujuan untuk membuat konfigurasi penempatan kendaraan paling optimal pada sebuah geladak kapal kargo. Setiap kendaraan dan geladak direpresentasikan sebagai grid dua dimensi berbentuk persegi atau persegi panjang. Solusi dapat memilih kendaraan mana yang diangkut dan menentukan posisi serta orientasinya di dalam geladak, dengan tetap memenuhi seluruh batasan.

![](data:image/png;base64...)

## Daftar Variabel Permasalahan

| **Entitas** | **Atribut** | **Contoh** | **Keterangan** |
| --- | --- | --- | --- |
| Vehicle | id | “Owen” | *Identifier* |
| Dimensions | {w:3, l:4} | Ukuran sebuah kendaraan, terdiri atas *width* dan *length* (satuan grid) |
| Orientation | Horizontal | *Horizontal* atau *Vertical* |
| ShippingFee | 60 | Tarif/keuntungan pengiriman kendaraan (satuan juta rupiah) |
| Weight | 5 | Berat kendaraan (satuan unit) |
| ETA | 3 | [Estimated Time of Arrival](https://www.shippeo.com/resources/explore/blog-newsletter/eta-meaning-in-business-a-critical-metric-for-supply-chain-success), perkiraan waktu kedatangan kendaraan (dalam sisa hari) |
| Ship | Dimensions | {w:10, l:20} | Ukuran geladak pada kapal, terdiri atas *width* dan *length* (satuan grid) |
| MaxCapacity | 500 | Kapasitas angkut maksimum suatu kapal (satuan unit) |

###

## Ketentuan Representasi

Berikut prosedur bagaimana dalam merepresentasikan permasalahan ini:

* Kendaraan dan geladak kapal direpresentasikan sebagai grid dua dimensi berbentuk persegi atau persegi panjang.
* Kendaraan dapat berbeda ukuran satu sama lain dan tidak semua harus dimasukkan ke dalam peti kemas pada kapal sehingga suatu kendaraan dapat berada di luar **(seluruh bagian kendaraan di luar kapal)**
* Koordinat berupa bilangan bulat. Cara representasi koordinat dibebaskan.
* Struktur data yang digunakan untuk representasi dibebaskan. Misalnya menggunakan *key-value* seperti JSON.
* Inisialisasi (***initial state***) random.
* Langkah neighbor (***move***) yang diperbolehkan tiap iterasi:

1. Menukar dua kendaraan, baik di dalam maupun di luar kapal
2. Memindahkan sebuah kendaraan ke suatu koordinat yang berbeda
3. Mengubah orientasi kendaraan

* Representasi solusi (***final state***) adalah pemetaan semua paket yang ada dan juga pemetaan semua koordinat dalam peti kemas pada kapal. Secara detail yang harus dapat ditunjukkan oleh state dan visualisasi adalah:
  1. Bagaimana keadaan semua kendaraan yang di dalam maupun yang di luar
  2. Bagaimana keadaan geladak pada kapal
  3. *Value* pada *state* tersebut

## Objective Function & Constraints

Agar permasalahan ini tidak menjadi kompleks, berikut arahan yang diberikan

* **Objective function**

Permasalahan ini bertujuan untuk memaksimalkan *ShippingFee* pada kapal.

* **Kendaraan tidak boleh saling bertumpuk (*no overlapping*)**

Tidak boleh ada satu sel grid geladak yang ditempati oleh lebih dari satu kendaraan.

* **Kendaraan harus berada di dalam batas geladak.**

Seluruh sel grid yang ditempati suatu kendaraan harus berada di dalam dimensi geladak kapal.

* **Kapal tidak boleh mengangkut melebihi kapasitasnya.**

# Cakupan

Anda akan diminta untuk mengimplementasikan rencana yang telah Anda buat pada Tugas Besar 1. Berikut merupakan hal-hal yang perlu dilakukan oleh setiap kelompok.

Implementasikan 3 algoritma *local search* dengan rincian sebagai berikut:

1. Salah satu algoritma Hill-climbing
2. Simulated Annealing
3. Genetic Algorithm

Jalankan setiap algoritma (selain Genetic Algorithm) sebanyak **3 kali**, kemudian catat beberapa hal berikut:

1. Berlaku untuk semua algoritma
   1. *State* awal dan akhir
   2. Nilai *objective function* akhir yang dicapai
   3. Plot nilai *objective function* terhadap banyak iterasi yang telah dilewati
   4. Durasi proses pencarian
2. Berlaku hanya untuk Steepest Ascent Hill-Climbing dan Stochastic Hill-climbing
   1. Banyak iterasi hingga proses pencarian berhenti
3. Berlaku hanya untuk Hill-Climbing with Sideways Move
   1. Banyak iterasi hingga proses pencarian berhenti
   2. Tambahkan parameter ***maximum sideways move***, dimana ketika banyak *sideways move* yang dilakukan sudah mencapai maksimum, pencarian dihentikan
4. Berlaku hanya untuk Random Restart Hill-climbing
   1. Banyak *restart*
   2. Banyak iterasi per *restart*
   3. Tambahkan parameter ***maximum restart***, dimana ketika banyak *restart* sudah mencapai maksimum, pencarian dihentikan.
5. Berlaku hanya untuk Simulated Annealing
   1. Plot $e^{\frac{ΔE}{T}}$ terhadap banyak iterasi yang telah dilewati
   2. Frekuensi ‘*stuck*’ di *local optima*

Khusus untuk Genetic Algorithm, lakukan beberapa hal berikut:

1. Terdapat 2 parameter yang dapat diubah, yaitu **jumlah populasi** dan **banyak iterasi.**
2. Jadikan jumlah populasi sebagai kontrol, kemudian pilih **3 variasi** banyak iterasi yang berbeda. Jalankan program sebanyak masing-masing **3 kali** untuk setiap konfigurasi parameter.
3. Jadikan banyak iterasi sebagai kontrol, kemudian pilih **3 variasi** jumlah populasi yang berbeda. Jalankan program sebanyak masing-masing **3 kali** untuk setiap konfigurasi parameter.
4. Untuk setiap eksperimen, catat beberapa hal berikut:
   1. *State* awal dan akhir
   2. Nilai *objective function* akhir yang dicapai
   3. Plot nilai *objective function* terhadap banyak iterasi yang telah dilewati (Cukup plot nilai *objective function* maksimum dan rata-rata dari populasi terhadap banyak iterasi yang telah dilewati.)
   4. Jumlah populasi
   5. Banyak iterasi
   6. Durasi proses pencarian

Lakukan analisis terhadap hasil eksperimen, berikut merupakan beberapa pertanyaan yang dapat menjadi acuan untuk analisis yang Anda lakukan:

1. Seberapa dekat tiap-tiap algoritma bisa mendekati *global optima* dan mengapa hasilnya demikian?
2. Bagaimana perbandingan hasil pencarian tiap-tiap algoritma dengan algoritma *local search* yang lain?
3. Bagaimana perbandingan durasi proses pencarian tiap algoritma relatif terhadap algoritma lainnya?
4. Seberapa konsisten hasil akhir yang didapatkan dari tiap-tiap eksperimen yang dilakukan?
5. Bagaimana pengaruh banyak iterasi dan jumlah populasi terhadap hasil akhir pencarian pada Genetic Algorithm?
6. dst…

Anda boleh mengganti dan/atau menambahkan beberapa pertanyaan jika dirasa perlu untuk memudahkan penjelasan.

Program yang dibuat harus bisa **memvisualisasikan** *initial state*, *final state* dan juga hasil eksperimennya (sesuaikan informasi hasil eksperimen yang ditampilkan dengan ketentuan yang telah dijelaskan di poin sebelum ini).

Gunakan bahasa **Python dalam implementasi *local search*.** Semua bahasa dan *library* boleh digunakan untuk **visualisasi** (misalnya ingin *web based*). Cara visualisasi tidak memengaruhi penilaian dan dibebaskan kepada masing-masing kelompok sedemikian rupa untuk memudahkan penjelasan saat demo nanti.

Diperbolehkan untuk menggunakan heuristik yang Anda buat sendiri atau dari referensi lain untuk optimasi pencarian solusi, asalkan masih dalam lingkup *local search*. Jelaskan *heuristik* yang Anda pakai di laporan.

#

# Bonus

Hanya kerjakan spesifikasi ini jika Anda sudah menyelesaikan seluruh spesifikasi wajib. Berikut merupakan beberapa spesifikasi bonus yang dapat Anda kerjakan:

1. Buatlah ***objective function*** selain yang telah didefinisikan, **tanpa menambah variabel yang ada**. (3 poin)
2. Buatlah implementasi untuk **seluruh algoritma Hill-climbing** yang ada.
   (7 poin)
3. **Multi-kapal**. Program dapat menerima jumlah kapal lebih dari satu dan memaksimalkan *value* **total**yang diangkut armada. (10 poin)

#

# Referensi

[1] M. L. Khodra, "Beyond Classical Search: Classical vs Local Search," YouTube, 2021. [Video]. Available: [Beyond Classical Search: Classical vs Local Search](https://www.youtube.com/watch?v=oGTa9kGE3P8.) [Accessed: Sep. 16, 2026].

[2] M. L. Khodra, "Beyond Classical Search: State (Value, Neighbor)," YouTube, 2021. [Video]. Available: <https://www.youtube.com/watch?v=_6rla37QorM>. [Accessed: Sep. 16, 2026].

[3] M. L. Khodra, "Beyond Classical Search: Hill-climbing Search," YouTube, 2021. [Video]. Available: <https://www.youtube.com/watch?v=L0b0CN3Fds8>. [Accessed: Sep. 16, 2026].

[4] M. L. Khodra, "Beyond Classical Search: Simulated Annealing," YouTube, 2021. [Video]. Available: [Beyond Classical Search: Simulated Annealing](https://www.youtube.com/watch?v=AdhG7HnhYrk.) [Accessed: Sep. 16, 2026].

[5] M. L. Khodra, "Beyond Classical Search: Genetic Algorithm," YouTube, 2021. [Video]. Available: [Beyond Classical Search: Genetic Algorithm](https://www.youtube.com/watch?v=aI41TGo9J9c.) [Accessed: Sep. 16, 2026].

# Salam dari Asisten

**dindazzly**
“jangan lupa qris dananya kak”

**Fathurwithyou**
“10.10 jangan lupa checkout”

**rzi**
“mohon maaf apabila kendaraannya telat datang 🧡”

**owen**
“persiapan magang di TXXXX Intim Line 😹”

**wwwwww**
“魔女の宅急便じゃないですよ”

**fififafa**

“Jangan lupa magang eh mangan”