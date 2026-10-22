# Perbandingan objective fee dan urgensi ETA

Bobot urgensi = fee * (1 + 1/(eta + 1)). Shipping fee asli tidak diubah dalam tabel ini.
Seed SA yang sama memakai penempatan initial yang sama. Gap setiap baris memakai UB objective-nya sendiri.
Baris fee hanya ditampilkan bila eksperimen pasangannya tersedia.

| Seed | Objective | Fee asli | Bobot urgensi | Dimuat | Mean ETA | Feasible | Gap UB |
|---|---|---|---|---|---|---|---|
| 1 | fee | 964 | 1243.45 | 11 | 3.82 | True | 6.9% |
| 1 | eta | 984 | 1293.30 | 16 | 3.62 | True | 3.9% |
| 2 | fee | 973 | 1206.80 | 15 | 4.20 | True | 6.0% |
| 2 | eta | 941 | 1223.58 | 16 | 3.44 | True | 9.1% |
| 3 | fee | 962 | 1148.13 | 17 | 4.29 | True | 7.1% |
| 3 | eta | 941 | 1228.80 | 15 | 3.80 | True | 8.7% |

