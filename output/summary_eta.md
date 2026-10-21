# Ringkasan Bonus 1: objective urgensi ETA

Algoritma `sa`, instance `main`, parameter default (`config.py`). Bobot urgensi w = fee * (1 + 1/(eta + 1)). Run fee dan run ETA dengan seed yang sama berangkat dari initial state yang sama.

| Seed | Objective | Fee asli | Bobot urgensi | Dimuat | Mean ETA dimuat | Feasible | Gap UB |
|---|---|---|---|---|---|---|---|
| 1 | fee | 964 | 1243.5 | 11 | 3.82 | True | 6.9% |
| 1 | eta | 984 | 1293.3 | 16 | 3.62 | True | 3.9% |
| 2 | fee | 973 | 1206.8 | 15 | 4.20 | True | 6.0% |
| 2 | eta | 941 | 1223.6 | 16 | 3.44 | True | 9.1% |
| 3 | fee | 962 | 1148.1 | 17 | 4.29 | True | 7.1% |
| 3 | eta | 941 | 1228.8 | 15 | 3.80 | True | 8.7% |

Gap UB tiap baris dihitung terhadap UB objective-nya sendiri (UB fee untuk run fee, UB bobot untuk run ETA). Durasi tidak dibandingkan di sini karena run fee resmi dijalankan pada kondisi mesin yang lain (EXPERIMENTS §4); durasi tiap run ada di JSON-nya.
