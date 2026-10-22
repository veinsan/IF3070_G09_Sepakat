# Bab 2 Pembahasan

## 2.8 Visualisasi

Modul visualisasi menampilkan keadaan satu *state* dan perkembangan pencarian setiap algoritma. Visualisasi diperlukan karena spesifikasi meminta *state* memperlihatkan keadaan semua kendaraan di dalam dan di luar kapal, keadaan geladak, serta value-nya, dan meminta hasil eksperimen disajikan dalam bentuk *plot*. Seluruh gambar dibuat dari *dictionary* hasil *run* yang tersimpan sebagai JSON di folder `output/`, bukan dari objek yang ada di memori saat pencarian berjalan. Dengan demikian, gambar *state* dan *plot* dapat dibuat ulang kapan saja tanpa menjalankan pencarian lagi, misalnya dengan `python src/main.py --view <file.json>` atau `python src/experiments.py --plots-only`. Modul memakai kelas `matplotlib.figure.Figure` secara langsung (tanpa `pyplot`), sehingga dapat berjalan tanpa tampilan grafis.

### 2.8.1 Cara Membaca Gambar State

Contoh berikut adalah *state* acak untuk *instance* multi-kapal (`multi.json`, 3 kapal), dibuat dengan `random_state(problem, random.Random(4))` lalu digambar dengan `draw_state`. *State* ini hanya ilustrasi, bukan hasil eksperimen, dan tidak *feasible* sehingga arsiran tumpang tindih dan garis keluar geladak terlihat.

<p align="center"><img src="DRAF-LAPORAN-L-gambar/contoh_state_multi.png" width="560"></p>

<p align="center"><i>Gambar 2.8.1.1 Contoh state acak instance multi-kapal (ilustrasi, bukan hasil eksperimen): objective -56817, tidak feasible dengan 97 sel overlap, 110 sel keluar batas, dan 128 unit kelebihan berat</i></p>

- **Panel per kapal.** Setiap kapal digambar pada panel sendiri. Judul panel berisi id kapal, ukuran geladak (lebar × panjang), banyak kendaraan yang dimuat, serta berat terpakai dibanding kapasitas. Bila berat melebihi kapasitas, judul panel diberi tanda "(MELEBIHI)". Untuk *instance* multi-kapal (Bonus 3) terdapat satu panel untuk setiap kapal.
- **Sumbu dan grid.** Area abu-abu muda bergaris tepi hitam adalah geladak. Nomor kolom (x) ada di atas dan nomor baris (y) di kiri. Sumbu y mengarah ke bawah, sehingga anchor `(x, y)` sebuah kendaraan adalah sel kiri-atasnya.
- **Kendaraan.** Setiap kendaraan berupa persegi panjang dengan warna tetap per kendaraan, berlabel id dan orientasinya (`H` atau `V`).
- **Tumpang tindih.** Sel yang ditempati lebih dari satu kendaraan diberi arsiran silang merah.
- **Keluar geladak.** Kendaraan yang sebagian berada di luar geladak digambar lebih transparan dengan tepi merah putus-putus, dan area gambar diperluas supaya bagian yang keluar tetap terlihat.
- **Judul gambar.** Baris pertama berisi keterangan *run* (*state* awal/akhir, algoritma, *instance*, *seed*). Baris kedua berisi *value*: *objective* dan total *fee*. Baris ketiga berisi status: "*feasible*", atau "TIDAK *feasible*" beserta rincian jumlah sel *overlap*, sel keluar batas, dan unit kelebihan berat.
- **Daftar kendaraan di luar kapal.** Panel kanan berjudul "Di luar kapal (n)" dan mencantumkan setiap kendaraan yang tidak dimuat beserta ukuran, *fee*, dan beratnya, dengan warna latar yang sama dengan warna kendaraan tersebut. Daftar dibagi dua kolom bila berisi lebih dari 24 kendaraan.

### 2.8.2 Isi Plot per Algoritma

Setiap *run* menghasilkan satu file `<run_id>_plot.png`. Judul gambar berisi algoritma, *instance*, *seed*, jumlah iterasi, dan durasi.

- **Objective vs iterasi (semua algoritma).** Garis *objective* *state* saat ini pada setiap iterasi, dengan judul berisi *objective* awal dan akhir. Garis putus-putus abu-abu menandai *upper bound*. Contoh: *plot* Steepest Ascent di bagian hasil eksperimen.
- **Random Restart.** Selain *objective* per iterasi (yang turun tajam setiap kali *restart* dimulai dari *state* acak baru), terdapat garis putus-putus "terbaik sejauh ini". Contoh: *plot* Random Restart di bagian hasil eksperimen.
- **Genetic Algorithm.** Sumbu x adalah generasi. Terdapat dua garis: *objective* maksimum populasi dan rata-rata *objective* populasi per generasi. Contoh: *plot* GA di bagian hasil eksperimen.
- **Simulated Annealing.** Panel kiri berisi *objective* vs iterasi. Panel kanan berisi sebaran nilai `e^(ΔE/T)` vs iterasi, hanya untuk iterasi dengan move yang memperburuk (ΔE < 0), dan judulnya mencantumkan jumlah kejadian *stuck*. Contoh: *plot* Simulated Annealing di bagian hasil eksperimen.
- **Ringkasan antar-algoritma.** `plot_summary` membuat dua panel: *box plot* *objective* akhir per kelompok, dengan titik hitam untuk setiap *run* dan garis *upper bound*, serta diagram batang rata-rata durasi pencarian. Gambarnya ada di bagian perbandingan antar-algoritma.

### 2.8.3 Daftar Fungsi

**`src/visualization/state_view.py`**

| Fungsi | Masukan | Keluaran | Kegunaan |
|---|---|---|---|
| `vehicle_color(i)` | index kendaraan | warna RGBA | Warna tetap untuk kendaraan ke-i, sama di semua gambar (palet 60 warna) |
| `draw_state(problem, state_data, title)` | instance, dict state (`State.to_dict()`), judul opsional | `Figure` | Menggambar satu panel per kapal dan satu panel daftar kendaraan di luar kapal, dengan judul berisi value dan status feasible |
| `_draw_deck(ax, state, s, used_weight)` | axes, `State`, index kapal, berat terpakai | – (menggambar di `ax`) | Grid geladak kapal ke-s, kendaraan beserta label, arsiran overlap, dan bagian yang keluar geladak |
| `_extent(state, s)` | `State`, index kapal | (batas kanan, batas bawah) | Memperluas area gambar bila ada kendaraan yang keluar geladak |
| `_draw_outside(ax, problem, state)` | axes, instance, `State` | – (menggambar di `ax`) | Daftar kendaraan di luar kapal beserta ukuran, fee, dan berat |
| `render_state_text(problem, state_data)` | instance, dict state | teks | Versi ASCII state untuk terminal: value, grid tiap geladak (`#` = overlap), daftar kendaraan di luar |
| `save_run_states(problem, result, prefix)` | instance, dict hasil run, prefix path | daftar path PNG | Menyimpan `<prefix>_initial.png` dan `<prefix>_final.png` |

**`src/visualization/plots.py`**

| Fungsi | Masukan | Keluaran | Kegunaan |
|---|---|---|---|
| `run_label(result)` | dict hasil run | teks | Label singkat `algoritma \| instance \| seed` |
| `plot_objective(ax, result)` | axes, dict hasil run | – (menggambar di `ax`) | Objective vs iterasi, ditambah garis terbaik sejauh ini (Random Restart), maksimum dan rata-rata populasi (GA), dan garis upper bound |
| `plot_acceptance(ax, result)` | axes, dict hasil run SA | – (menggambar di `ax`) | Sebaran `e^(ΔE/T)` vs iterasi dan jumlah kejadian stuck |
| `plot_run(result, path)` | dict hasil run, path opsional | `Figure` | Semua plot satu run dalam satu gambar (SA: dua panel), disimpan bila `path` diberikan |
| `plot_summary(results, path, group)` | daftar hasil run, path opsional, fungsi pengelompokan | `Figure` | Box plot objective akhir dan rata-rata durasi per algoritma atau per konfigurasi |
| `_save(fig, path)` | `Figure`, path | – | Membuat folder bila perlu dan menyimpan PNG (dpi 150) |

### 2.8.4 Source Code

Berikut source code fungsi `draw_state` pada file `src/visualization/state_view.py`.

```python
def draw_state(problem: Problem, state_data: dict[str, Any], title: str = "") -> Figure:
    """Gambar satu state (dict hasil `State.to_dict()`) sebagai Figure.

    Panel ke-k adalah geladak kapal ke-k (axes label `deck:<id>`), panel terakhir daftar kendaraan di luar
    kapal (axes label `outside`). Judul memuat objective, total fee, jumlah pelanggaran, dan status feasible.
    """
    state = State.from_dict(problem, state_data)
    evaluation = state.evaluate()
    ships = problem.ships

    max_rows = max(ship.length for ship in ships)
    # +2 sel per panel geladak sebagai ruang untuk bagian kendaraan yang keluar batas dan label sumbu
    ratios = [ship.width + 2 for ship in ships] + [OUTSIDE_PANEL_CELLS]
    fig = Figure(figsize=(CELL_INCH * sum(ratios), CELL_INCH * (max_rows + 6)), layout="constrained")
    axes = fig.subplots(1, len(ratios), gridspec_kw={"width_ratios": ratios})

    for s, (ship, ax) in enumerate(zip(ships, axes)):
        _draw_deck(ax, state, s, evaluation.used_weight[s])
    _draw_outside(axes[-1], problem, state)

    status = "feasible" if evaluation.is_feasible else (
        f"TIDAK feasible (overlap {evaluation.overlap_cells} sel, keluar batas {evaluation.out_of_bound_cells} sel, "
        f"kelebihan berat {evaluation.weight_units} unit)"
    )
    # status di baris sendiri: rincian pelanggaran state tidak feasible lebih lebar dari geladak kecil
    header = f"objective = {evaluation.objective:g} | total fee = {evaluation.total_fee:g}\n{status}"
    fig.suptitle(f"{title}\n{header}" if title else header, fontsize=10)
    return fig
```

Berikut source code fungsi `plot_objective` dan `plot_summary` pada file `src/visualization/plots.py`.

```python
def plot_objective(ax, result: Result) -> None:
    """Objective vs iterasi pada `ax`. GA: maksimum dan rata-rata populasi. Random Restart: plus terbaik."""
    history = result["history"]
    objective = history["objective"]
    is_population = "mean" in history
    ax.plot(range(len(objective)), objective, linewidth=1,
            label="maksimum populasi" if is_population else "objective")
    if is_population:
        ax.plot(range(len(history["mean"])), history["mean"], linewidth=1, label="rata-rata populasi")
    if "best" in history:
        ax.plot(range(len(history["best"])), history["best"], linewidth=1.2, linestyle="--", label="terbaik sejauh ini")
    if result.get("upper_bound") is not None:
        ax.axhline(result["upper_bound"], color="gray", linewidth=0.8, linestyle=":",
                   label=f"upper bound ({result['upper_bound']:g})")
    ax.set_xlabel("generasi" if is_population else "iterasi")
    ax.set_ylabel("objective")
    ax.set_title(f"Objective vs {'generasi' if is_population else 'iterasi'} | awal {result['initial_objective']:g}"
                 f" → akhir {result['final_objective']:g}", fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)


def plot_summary(
    results: Sequence[Result],
    path: str | Path | None = None,
    group: Callable[[Result], str] = lambda r: r["algorithm"],
) -> Figure:
    """Ringkasan antar-algoritma: box plot objective akhir dan rata-rata durasi per kelompok `group`.

    Default dikelompokkan per algoritma. Untuk GA bisa per konfigurasi, misalnya
    `group=lambda r: f"pop {r['params']['population']}"`.
    """
    groups: dict[str, list[Result]] = {}
    for result in results:
        groups.setdefault(group(result), []).append(result)
    labels = list(groups)

    fig = Figure(figsize=(max(7, 1.6 * len(labels) + 2), 4.5), layout="constrained")
    ax_obj, ax_time = fig.subplots(1, 2)
    finals = [[r["final_objective"] for r in groups[k]] for k in labels]
    ax_obj.boxplot(finals)
    # label diset terpisah: argumen label boxplot berganti nama di matplotlib 3.9 (requirements: >= 3.8)
    ax_obj.set_xticks(range(1, len(labels) + 1), labels=labels)
    # tiap kelompok hanya beberapa run (3 seed), jadi nilai per run ikut ditampilkan
    for k, values in enumerate(finals, start=1):
        ax_obj.scatter([k] * len(values), values, s=12, color="black", alpha=0.6, zorder=3)
    bounds = {r.get("upper_bound") for r in results}
    if len(bounds) == 1 and None not in bounds:
        ax_obj.axhline(bounds.pop(), color="gray", linewidth=0.8, linestyle=":", label="upper bound")
        ax_obj.legend(fontsize=7)
    ax_obj.set_ylabel("objective akhir")
    ax_obj.set_title("Objective akhir", fontsize=9)

    ax_time.bar(labels, [mean(r["duration_s"] for r in groups[k]) for k in labels])
    ax_time.set_ylabel("durasi rata-rata (s)")
    ax_time.set_title("Durasi pencarian", fontsize=9)
    for ax in (ax_obj, ax_time):
        ax.tick_params(axis="x", labelrotation=30, labelsize=8)
        ax.grid(axis="y", alpha=0.3)

    if path is not None:
        _save(fig, path)
    return fig
```

## 2.9 Program: CLI dan Runner Eksperimen

### 2.9.1 CLI (src/main.py)

CLI menjadi pintu masuk untuk menjalankan satu algoritma pada satu *instance*. Pengguna memilih algoritma, *instance*, *seed*, dan parameter melalui opsi baris perintah. Parameter yang tidak diisi memakai nilai *default* di `src/config.py`, dan parameter yang tidak berlaku untuk algoritma yang dipilih ditolak. Setelah pencarian selesai, CLI mencetak ringkasan hasil dan final *state* dalam bentuk teks, lalu menyimpan hasil lengkap sebagai JSON beserta gambar *state* awal, *state* akhir, dan *plot*. Opsi `--view` membuka kembali hasil yang sudah tersimpan tanpa menjalankan pencarian, termasuk hasil Bonus 1. Fungsi-fungsi CLI juga dipakai oleh *runner* eksperimen, sehingga hasil *run* lewat CLI dan lewat *runner* identik.

#### 2.9.1.1 Opsi CLI

| Opsi | Keterangan | Contoh |
|---|---|---|
| `--algo` | `steepest` (alias `hc`), `sideways`, `random_restart`, `stochastic`, `sa`, `ga`; wajib kecuali memakai `--view` | `python src/main.py --algo hc --seed 1` |
| `--instance` | file instance JSON, default `main.json`; nama file di `src/data/` juga diterima | `python src/main.py --algo sa --instance multi.json --seed 2` |
| `--seed` | seed random, default 1 | `python src/main.py --algo sa --seed 3` |
| `--objective` | objective yang dioptimasi; hanya `fee` (Bonus 1 dijalankan lewat `src/eta_experiments.py`) | `python src/main.py --algo sa --objective fee` |
| `--max-sideways` | batas total sideways move (`sideways`) | `python src/main.py --algo sideways --max-sideways 10` |
| `--max-restart` | banyak restart (`random_restart`) | `python src/main.py --algo random_restart --max-restart 5` |
| `--max-no-improve` | batas percobaan berturut-turut tanpa perbaikan (`stochastic`) | `python src/main.py --algo stochastic --max-no-improve 5000` |
| `--max-iterations` | batas pengaman iterasi varian HC (Random Restart: per percobaan) | `python src/main.py --algo steepest --max-iterations 50` |
| `--iterations` | iterasi SA atau generasi GA | `python src/main.py --algo sa --iterations 50000` |
| `--population` | ukuran populasi GA | `python src/main.py --algo ga --population 50 --iterations 300 --seed 3` |
| `--out` | folder output, default `output/` | `python src/main.py --algo hc --out tmp_demo` |
| `--no-save` | hanya menampilkan hasil, tidak menulis file | `python src/main.py --algo sa --no-save` |
| `--no-plot` | menyimpan JSON tanpa gambar | `python src/main.py --algo ga --no-plot` |
| `--view JSON` | menampilkan dan menggambar ulang hasil tersimpan tanpa pencarian | `python src/main.py --view output/sa/main_seed1.json` |

#### 2.9.1.2 Pola run_id dan File Output

Hasil satu *run* disimpan di `<out>/<algoritma>/`. Nama file (`run_id`) adalah `<instance>_seed<seed>`, misalnya `output/sa/main_seed1`. Untuk GA, ukuran populasi dan banyak generasi ikut dicantumkan karena eksperimen GA memvariasikan keduanya: `<instance>_pop<P>_iter<I>_seed<seed>`, misalnya `output/ga/main_pop50_iter1000_seed2`. Run Bonus 1 memakai *instance* turunan bernama `main_eta`, sehingga namanya `output/sa/main_eta_seed1` dan tidak menimpa *run* *objective* *fee*. Setiap *run* menghasilkan empat file:

| File | Isi |
|---|---|
| `<run_id>.json` | Hasil lengkap run: algoritma, instance, seed, parameter, state awal dan akhir (penempatan semua kendaraan dan grid tiap geladak), objective awal dan akhir, total fee, feasibility dan pelanggaran, berat per kapal, upper bound, gap, durasi, iterasi, evaluasi, history, dan info khusus algoritma |
| `<run_id>_initial.png` | Gambar state awal |
| `<run_id>_final.png` | Gambar state akhir |
| `<run_id>_plot.png` | Plot objective vs iterasi (GA: maksimum dan rata-rata populasi; SA: ditambah `e^(ΔE/T)`) |

Durasi di JSON (`duration_s`) adalah durasi pencarian saja, tidak termasuk waktu menyimpan file dan gambar.

#### 2.9.1.3 Daftar Fungsi

| Fungsi | Masukan | Keluaran | Kegunaan |
|---|---|---|---|
| `ALGORITHMS` (tabel) | – | nama algoritma → (fungsi, pemetaan opsi CLI ke parameter fungsi) | Registri enam algoritma, ditambah alias `hc` = `steepest` |
| `run_algorithm(algo, problem, seed, **params)` | nama algoritma, instance, seed, parameter dengan nama opsi CLI | `RunResult` | Menjalankan algoritma dan menolak parameter yang tidak berlaku |
| `run_id(result)` | dict hasil run | teks | Nama file hasil run (lihat bagian pola `run_id` dan file output) |
| `save_run(result, problem, out_dir, plots)` | dict hasil run, instance, folder output | daftar path | Menyimpan JSON dan, bila `plots`, gambar state dan plot |
| `save_plots(result, problem, prefix)` | dict hasil run, instance, prefix path | daftar path PNG | Menyimpan `_initial.png`, `_final.png`, dan `_plot.png` |
| `format_summary(result)` | dict hasil run | teks | Ringkasan terminal: parameter, objective awal dan akhir, total fee, upper bound, gap, feasibility, muatan, iterasi, evaluasi, durasi, info khusus algoritma |
| `resolve_instance(value)` | path atau nama file | `Path` | Menerima path lengkap atau nama file di `src/data/` (misalnya `multi.json` atau `multi`) |
| `view_problem(result, instance)` | dict hasil run, instance opsional | `Problem` | Instance untuk `--view`; hasil Bonus 1 (`<nama>_eta`) memakai instance turunan bobot urgensi |
| `build_parser()` | – | `ArgumentParser` | Definisi opsi CLI |
| `main(argv)` | argumen baris perintah | kode keluar | Validasi argumen, menjalankan atau membuka hasil, mencetak, dan menyimpan |

#### 2.9.1.4 Source Code

Berikut source code fungsi `run_algorithm` dan `run_id` pada file `src/main.py`.

```python
def run_algorithm(algo: str, problem: Problem, seed: int, **params: Any) -> RunResult:
    """Jalankan algoritma `algo` (nama di `ALGORITHMS` atau alias) dengan parameter opsional `params`.

    `params` memakai nama opsi CLI (misalnya `population`), bukan nama parameter fungsi.
    """
    algo = ALIASES.get(algo, algo)
    function, mapping = ALGORITHMS[algo]
    unknown = set(params) - set(mapping)
    if unknown:
        raise ValueError(f"parameter {', '.join(sorted(unknown))} tidak berlaku untuk algoritma {algo}")
    return function(problem, seed=seed, **{mapping[k]: v for k, v in params.items()})


def run_id(result: dict[str, Any]) -> str:
    """Nama file satu run tanpa ekstensi, misalnya `main_seed1` atau `main_pop50_iter300_seed2` (GA)."""
    if result["algorithm"] == "ga":
        params = result["params"]
        return f"{result['instance']}_pop{params['population']}_iter{params['iterations']}_seed{result['seed']}"
    return f"{result['instance']}_seed{result['seed']}"
```

### 2.9.2 Runner Eksperimen (src/experiments.py)

Runner eksperimen (`src/experiments.py`) menjalankan seluruh *run* yang direncanakan di dokumen eksperimen dengan satu perintah, lalu menulis tabel ringkasan. Setiap *run* dijalankan dan disimpan dengan fungsi yang sama dengan CLI (`run_algorithm` dan `save_run`), sehingga hasilnya identik dengan *run* satu per satu lewat CLI. Semua *run* memakai *seed* 1, 2, dan 3 serta *instance* yang sama, sehingga hasil dapat diulang dan dibandingkan antar-algoritma. Runner juga dapat menggambar ulang semua gambar dan menulis ulang ringkasan dari JSON yang sudah ada tanpa menjalankan pencarian. Notebook `notebooks/experiments.ipynb` membaca JSON yang sama untuk menampilkan tabel, *plot*, dan gambar *state* di satu tempat.

#### 2.9.2.1 Grup Eksperimen

| Grup | Tabel hasil | Isi | Wajib | Run unik |
|---|---|---|---|---|
| `hc` | Steepest Ascent | Steepest Ascent HC, `main.json` | ya | 3 |
| `sa` | Simulated Annealing | Simulated Annealing, `main.json` | ya | 3 |
| `ga_iter` | GA variasi generasi | GA populasi 100, generasi 300 / 1000 / 3000 | ya | 9 |
| `ga_pop` | GA variasi populasi | GA generasi 1000, populasi 50 / 100 / 200 | ya | 6 (konfigurasi 100/1000 sudah dihitung di `ga_iter`) |
| `hc_variants` | Stochastic, Sideways Move, Random Restart | Varian HC Bonus 2 | tidak | 9 |
| `multi` | Multi-kapal | Steepest Ascent HC, `multi.json` (Bonus 3) | tidak | 3 |
| `eta` | Bonus 1 | SA dengan objective urgensi ETA | tidak | 3 |
| **Total** | | | | **21 wajib, 36 dengan semua bonus** (33 tanpa Bonus 1) |

Konfigurasi kontrol GA (populasi 100, generasi 1000) dipakai bersama oleh tabel variasi generasi dan tabel variasi populasi, sehingga hanya dijalankan sekali per *seed*. Run Bonus 1 dijalankan oleh `src/eta_experiments.py` (bagian T). Grup `eta` di *runner* memakai fungsi yang sama dan menghasilkan file yang sama.

#### 2.9.2.2 Isi output/summary.md dan Notebook

`output/summary.md` berisi waktu pembuatan, informasi mesin, jumlah *run* yang tersedia (36), lalu satu tabel untuk setiap jenis eksperimen: empat varian HC dan SA (per *seed* ditambah baris mean ± std), GA variasi generasi dan variasi populasi (per konfigurasi), multi-kapal (dengan berat dan banyak kendaraan per kapal), ringkasan antar-algoritma, dan Bonus 1. Bagian akhir menautkan tiga gambar ringkasan `summary_algorithms.png`, `summary_ga_iter.png`, dan `summary_ga_pop.png`. Perbandingan *run* *objective* *fee* dan *objective* ETA pada *seed* yang sama ada di `output/summary_eta.md`, yang ditulis oleh `src/eta_experiments.py`.

Notebook `notebooks/experiments.ipynb` tidak menjalankan pencarian. Isinya:

1. Memuat hasil: membaca semua `output/**/*.json` dan mencocokkannya dengan rencana *run* (36 dari 36 tersedia).
2. Tabel hasil per jenis eksperimen, sama dengan isi `summary.md`.
3. Plot per algoritma atau konfigurasi: satu baris per kelompok, satu kolom per *seed*; ditambah *plot* SA dengan `e^(ΔE/T)`.
4. *State* awal dan akhir *run* terbaik setiap algoritma.
5. Ringkasan antar-algoritma: *box plot*, perbandingan konfigurasi GA, dan kurva konvergensi (*objective* terbaik sejauh ini terhadap jumlah evaluasi, skala log).
6. Analisis singkat: kualitas hasil, jarak ke *upper bound*, durasi (termasuk hasil ukur ulang), dan konsistensi.

#### 2.9.2.3 Daftar Fungsi dan Opsi

| Fungsi / kelas | Masukan | Keluaran | Kegunaan |
|---|---|---|---|
| `Run` (dataclass) | grup, algoritma, instance, seed, parameter, objective | – | Satu run yang direncanakan; properti `run_id`, `required` (termasuk run wajib), dan `path(out_dir)` |
| `planned_runs(quick, seeds)` | mode cepat, daftar seed | daftar `Run` | Seluruh run tanpa duplikat; run kontrol GA tercatat di dua grup |
| `select(runs, only)` | daftar run, nama grup | daftar `Run` | Memilih run dari grup tertentu (`--only`) |
| `count_line(runs)` | daftar run | teks | "21 run wajib, 36 run dengan bonus" |
| `describe(run, out_dir, skip_existing)` | run, folder, opsi | teks | Satu baris daftar untuk `--dry-run` |
| `problem_for(run, problems)` | run, cache instance | `Problem` | Instance asli, atau instance turunan bobot urgensi untuk run Bonus 1 |
| `search(run, problem)` | run, instance | `RunResult` | Menjalankan pencarian; run Bonus 1 lewat `run_eta` (sama dengan `src/eta_experiments.py`) |
| `execute(runs, out_dir, skip_existing, plots)` | daftar run, folder, opsi | daftar path JSON | Menjalankan dan menyimpan semua run |
| `redraw(runs, out_dir)` | daftar run, folder | jumlah run | Menggambar ulang state dan plot dari JSON tanpa pencarian |
| `load_result(path)`, `load_results(runs, out_dir)` | path / daftar run | dict / pasangan (run, hasil) | Membaca JSON hasil run |
| `machine_info()` | – | teks | Sistem operasi, CPU, jumlah thread, dan versi Python |
| `summary_sections(pairs)` | pasangan (run, hasil) | baris Markdown | Tabel hasil per jenis eksperimen (varian HC, SA, GA, multi-kapal, ringkasan antar-algoritma, Bonus 1), termasuk baris mean ± std |
| `vehicles_per_ship(result)` | dict hasil run | daftar angka | Banyak kendaraan per kapal (Bonus 3) |
| `comparison_groups(pairs)` | pasangan (run, hasil) | dict | Kelompok perbandingan antar-algoritma; GA diwakili konfigurasi dengan mean terbaik |
| `write_summary(pairs, out_dir, missing, plots)` | pasangan, folder, run yang belum ada | path | Menulis `output/summary.md` dan `summary_*.png` |
| `main(argv)` | argumen | kode keluar | CLI runner |

**Opsi `experiments.py`**

| Opsi | Keterangan |
|---|---|
| (tanpa opsi) | Menjalankan semua run ke `output/`, lalu menulis `output/summary.md` |
| `--only GRUP ...` | Hanya grup tertentu: `hc`, `sa`, `ga_iter`, `ga_pop`, `hc_variants`, `eta`, `multi` |
| `--skip-existing` | Melewati run yang JSON-nya sudah ada (melanjutkan run yang terputus) |
| `--dry-run` | Menampilkan daftar run tanpa menjalankan |
| `--plots-only` | Tanpa pencarian: menggambar ulang dari JSON lalu menulis ringkasan |
| `--quick` | `small.json` dan parameter kecil, untuk uji coba dan test |
| `--no-plot` | Hanya JSON dan `summary.md`, tanpa gambar |
| `--out FOLDER` | Folder output, default `output/` |

#### 2.9.2.4 Source Code

Berikut source code fungsi `planned_runs` dan `write_summary` pada file `src/experiments.py`.

```python
def planned_runs(quick: bool = False, seeds: Sequence[int] = SEEDS) -> list[Run]:
    """Semua run eksperimen, tanpa duplikat (run kontrol GA tercatat di dua grup).

    `quick`: `small.json` menggantikan `main.json` dan semua parameter diperkecil, untuk test dan uji coba.
    """
    if quick:
        main_instance = resolve_instance("small.json")
        ga_population, ga_iterations = 10, 10
        ga_pop_variants, ga_iter_variants = (6, 10, 14), (5, 10, 15)
        hc = {"max_iterations": 3}
        params = {
            "steepest": {}, "sa": {"iterations": 500},
            "stochastic": {"max_no_improve": 200, "max_iterations": 1000},
            "sideways": {"max_sideways": 5, "max_iterations": 20},
            "random_restart": {"max_restart": 1, "max_iterations": 20},
            # multi.json: Steepest butuh ~0.5 s per iterasi
            "multi": hc,
        }
    else:
        main_instance = DEFAULT_INSTANCE
        ga_population, ga_iterations = GA_POPULATION, GA_ITERATIONS
        ga_pop_variants, ga_iter_variants = GA_POPULATION_VARIANTS, GA_ITERATION_VARIANTS
        # parameter lain = default fungsi (config.py)
        params = {"steepest": {}, "sa": {}, "stochastic": {}, "sideways": {}, "random_restart": {}, "multi": {}}

    runs: dict[tuple[str, str], Run] = {}

    def add(group: str, algo: str, instance: Path, extra: dict[str, int], objective: str = "fee") -> None:
        for seed in seeds:
            run = Run((group,), algo, instance, seed, dict(extra), objective)
            key = (run.algo, run.run_id)
            if key in runs:
                runs[key].groups += (group,)
            else:
                runs[key] = run

    add("hc", "steepest", main_instance, params["steepest"])
    add("sa", "sa", main_instance, params["sa"])
    for iterations in ga_iter_variants:
        add("ga_iter", "ga", main_instance, {"population": ga_population, "iterations": iterations})
    for population in ga_pop_variants:
        add("ga_pop", "ga", main_instance, {"population": population, "iterations": ga_iterations})
    for algo in ("stochastic", "sideways", "random_restart"):
        add("hc_variants", algo, main_instance, params[algo])
    # Bonus 1: SA dengan parameter §4.5, sama dengan src/eta_experiments.py (EXPERIMENTS §4.10)
    add("eta", "sa", main_instance, params["sa"], objective="eta")
    add("multi", "steepest", MULTI_INSTANCE, params["multi"])
    return list(runs.values())


def write_summary(pairs: Sequence[tuple[Run, Result]], out_dir: Path, missing: Sequence[Run] = (),
                  plots: bool = True) -> Path:
    """Tulis `<out_dir>/summary.md` (tabel per bagian EXPERIMENTS §4 + info mesin) dan `summary_*.png`."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Ringkasan eksperimen",
        "",
        f"Dibuat oleh `src/experiments.py` pada {time.strftime('%Y-%m-%d %H:%M')}.",
        f"Mesin: {machine_info()}.",
        f"Run tersedia: {len(pairs)}. Durasi = search saja (`duration_s`), tidak termasuk menyimpan file dan gambar.",
    ]
    if missing:
        lines.append(f"Belum ada / dilewati ({len(missing)}): " + ", ".join(f"`{r.algo}/{r.run_id}`" for r in missing))
    lines.extend(summary_sections(pairs))

    if plots and pairs:
        from visualization.plots import plot_summary

        images = []
        compare = comparison_groups(pairs)
        if compare:
            label = {id(r): k for k, results in compare.items() for r in results}
            plot_summary([r for results in compare.values() for r in results], out_dir / "summary_algorithms.png",
                         group=lambda r: label[id(r)])
            images.append("summary_algorithms.png")
        for group, key, name in (("ga_iter", "iterations", "iter"), ("ga_pop", "population", "pop")):
            results = sorted((res for run, res in pairs if group in run.groups), key=lambda r: r["params"][key])
            if results:
                plot_summary(results, out_dir / f"summary_{group}.png", group=lambda r: f"{name} {r['params'][key]}")
                images.append(f"summary_{group}.png")
        lines.extend(["", "### Gambar ringkasan", ""] + [f"![{img}]({img})" for img in images])

    path = out_dir / "summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
```

## 2.10 Hasil Eksperimen

Instance utama `src/data/main.json` (30 kendaraan, geladak 10×20, kapasitas 131, UB = 1035). Seed 1, 2, 3. Tabel disalin apa adanya dari `output/summary.md` (`True` = *feasible*). Keterangan dan analisis per algoritma diisi oleh pemilik algoritmanya: Hill-Climbing dan Bonus 3 oleh Riantama, SA, GA, dan Bonus 1 oleh Tiara.

### 2.10.1 Steepest Ascent Hill-Climbing

Parameter: `max_iterations = 10000`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/steepest/main_seed1_initial.png" width="320"><br><i>Gambar 2.10.1.1 State Awal Trial 1</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/steepest/main_seed1_final.png" width="320"><br><i>Gambar 2.10.1.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/steepest/main_seed1_plot.png" width="320"><br><i>Gambar 2.10.1.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/steepest/main_seed2_initial.png" width="320"><br><i>Gambar 2.10.1.4 State Awal Trial 2</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/steepest/main_seed2_final.png" width="320"><br><i>Gambar 2.10.1.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/steepest/main_seed2_plot.png" width="320"><br><i>Gambar 2.10.1.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/steepest/main_seed3_initial.png" width="320"><br><i>Gambar 2.10.1.7 State Awal Trial 3</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/steepest/main_seed3_final.png" width="320"><br><i>Gambar 2.10.1.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/steepest/main_seed3_plot.png" width="320"><br><i>Gambar 2.10.1.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | Evals | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | -21226 | 982 | 982 | True | 5.1% | 16 | 208452 | 5.628 |
| 2 | 2 | -50553 | 978 | 978 | True | 5.5% | 20 | 258031 | 9.368 |
| 3 | 3 | -28402 | 902 | 902 | True | 12.9% | 17 | 221238 | 6.997 |
| **mean ± std** |  |  | 954.0 ± 45.1 | 954.0 ± 45.1 |  |  |  |  | 7.331 ± 1.892 |

<mark>[diisi Riantama]</mark>

### 2.10.2 Stochastic Hill-Climbing (Bonus 2)

Parameter: `max_no_improve = 20000`, `max_iterations = 200000`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed1_initial.png" width="320"><br><i>Gambar 2.10.2.1 State Awal Trial 1</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed1_final.png" width="320"><br><i>Gambar 2.10.2.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed1_plot.png" width="320"><br><i>Gambar 2.10.2.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed2_initial.png" width="320"><br><i>Gambar 2.10.2.4 State Awal Trial 2</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed2_final.png" width="320"><br><i>Gambar 2.10.2.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed2_plot.png" width="320"><br><i>Gambar 2.10.2.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed3_initial.png" width="320"><br><i>Gambar 2.10.2.7 State Awal Trial 3</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed3_final.png" width="320"><br><i>Gambar 2.10.2.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/stochastic/main_seed3_plot.png" width="320"><br><i>Gambar 2.10.2.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | Evals | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | -21226 | 778 | 778 | True | 24.8% | 36486 | 36486 | 0.850 |
| 2 | 2 | -50553 | 876 | 876 | True | 15.4% | 32510 | 32510 | 0.854 |
| 3 | 3 | -28402 | 771 | 771 | True | 25.5% | 24504 | 24504 | 1.214 |
| **mean ± std** |  |  | 808.3 ± 58.7 | 808.3 ± 58.7 |  |  |  |  | 0.973 ± 0.209 |

<mark>[diisi Riantama]</mark>

### 2.10.3 Hill-Climbing with Sideways Move (Bonus 2)

Parameter: `max_sideways = 100`, `max_iterations = 10000`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/sideways/main_seed1_initial.png" width="320"><br><i>Gambar 2.10.3.1 State Awal Trial 1</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sideways/main_seed1_final.png" width="320"><br><i>Gambar 2.10.3.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sideways/main_seed1_plot.png" width="320"><br><i>Gambar 2.10.3.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/sideways/main_seed2_initial.png" width="320"><br><i>Gambar 2.10.3.4 State Awal Trial 2</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sideways/main_seed2_final.png" width="320"><br><i>Gambar 2.10.3.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sideways/main_seed2_plot.png" width="320"><br><i>Gambar 2.10.3.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/sideways/main_seed3_initial.png" width="320"><br><i>Gambar 2.10.3.7 State Awal Trial 3</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sideways/main_seed3_final.png" width="320"><br><i>Gambar 2.10.3.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sideways/main_seed3_plot.png" width="320"><br><i>Gambar 2.10.3.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | #Sideways | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | -21226 | 982 | 982 | True | 5.1% | 116 | 100 | 48.765 |
| 2 | 2 | -50553 | 978 | 978 | True | 5.5% | 120 | 100 | 49.008 |
| 3 | 3 | -28402 | 960 | 960 | True | 7.2% | 118 | 100 | 48.126 |
| **mean ± std** |  |  | 973.3 ± 11.7 | 973.3 ± 11.7 |  |  |  |  | 48.633 ± 0.455 |

<mark>[diisi Riantama]</mark>

### 2.10.4 Random Restart Hill-Climbing (Bonus 2)

Parameter: `max_restart = 10`, `max_iterations = 10000`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed1_initial.png" width="320"><br><i>Gambar 2.10.4.1 State Awal Trial 1</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed1_final.png" width="320"><br><i>Gambar 2.10.4.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed1_plot.png" width="320"><br><i>Gambar 2.10.4.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed2_initial.png" width="320"><br><i>Gambar 2.10.4.4 State Awal Trial 2</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed2_final.png" width="320"><br><i>Gambar 2.10.4.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed2_plot.png" width="320"><br><i>Gambar 2.10.4.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed3_initial.png" width="320"><br><i>Gambar 2.10.4.7 State Awal Trial 3</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed3_final.png" width="320"><br><i>Gambar 2.10.4.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/random_restart/main_seed3_plot.png" width="320"><br><i>Gambar 2.10.4.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj akhir | Fee | Feasible | Gap UB | #Restart | Iterasi per restart | Durasi (s) |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | 982 | 982 | True | 5.1% | 10 | 16, 14, 20, 17, 16, 15, 17, 17, 23, 16, 22 | 79.324 |
| 2 | 2 | 993 | 993 | True | 4.1% | 10 | 20, 18, 17, 13, 22, 14, 15, 22, 18, 18, 18 | 78.999 |
| 3 | 3 | 946 | 946 | True | 8.6% | 10 | 17, 23, 17, 16, 20, 16, 20, 19, 17, 18, 14 | 77.767 |
| **mean ± std** |  | 973.7 ± 24.6 | 973.7 ± 24.6 |  |  |  |  | 78.697 ± 0.821 |

<mark>[diisi Riantama]</mark>

### 2.10.5 Simulated Annealing

Parameter: `iterations = 100000`, `t_min = 0.01`, `t0_samples = 100`, `t0_accept = 0.8`, `stuck_window = 500`, `initial_p_inside = 0.5`. Nilai aktual per *run* (*seed* 1 / 2 / 3): `T0` = 12153.52 / 8142.36 / 13226.03, `α` = 0.999860 / 0.999864 / 0.999859.

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/sa/main_seed1_initial.png" width="320"><br><i>Gambar 2.10.5.1 State Awal Trial 1</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_seed1_final.png" width="320"><br><i>Gambar 2.10.5.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_seed1_plot.png" width="320"><br><i>Gambar 2.10.5.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/sa/main_seed2_initial.png" width="320"><br><i>Gambar 2.10.5.4 State Awal Trial 2</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_seed2_final.png" width="320"><br><i>Gambar 2.10.5.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_seed2_plot.png" width="320"><br><i>Gambar 2.10.5.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/sa/main_seed3_initial.png" width="320"><br><i>Gambar 2.10.5.7 State Awal Trial 3</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_seed3_final.png" width="320"><br><i>Gambar 2.10.5.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_seed3_plot.png" width="320"><br><i>Gambar 2.10.5.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Iterasi | #Stuck | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | -21226 | 964 | 964 | True | 6.9% | 100000 | 182 | 7.037 |
| 2 | 2 | -50553 | 973 | 973 | True | 6.0% | 100000 | 185 | 6.651 |
| 3 | 3 | -28402 | 962 | 962 | True | 7.1% | 100000 | 179 | 6.186 |
| **mean ± std** |  |  | 966.3 ± 5.9 | 966.3 ± 5.9 |  |  |  |  | 6.625 ± 0.426 |

<mark>[diisi Tiara]</mark>

### 2.10.6 Genetic Algorithm

#### 2.10.6.1 Variasi Banyak Generasi (Populasi Kontrol 100)

Parameter: `population = 100`, `iterations` = 300 / 1000 / 3000, `p_c = 0.8`, `p_m = 0.2`, `elitism = 2`, `epsilon = 1.0`, `selection = roulette`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Pop 100, Iter 300** | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter300_seed1_initial.png" width="320"><br><i>Gambar 2.10.6.1.1 State Awal Pop 100, Iter 300</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter300_seed1_final.png" width="320"><br><i>Gambar 2.10.6.1.2 State Akhir Pop 100, Iter 300</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter300_seed1_plot.png" width="320"><br><i>Gambar 2.10.6.1.3 Plot Nilai Objektif Pop 100, Iter 300</i> |  |
| **Pop 100, Iter 1000** | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter1000_seed1_initial.png" width="320"><br><i>Gambar 2.10.6.1.4 State Awal Pop 100, Iter 1000</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter1000_seed1_final.png" width="320"><br><i>Gambar 2.10.6.1.5 State Akhir Pop 100, Iter 1000</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter1000_seed1_plot.png" width="320"><br><i>Gambar 2.10.6.1.6 Plot Nilai Objektif Pop 100, Iter 1000</i> |  |
| **Pop 100, Iter 3000** | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter3000_seed1_initial.png" width="320"><br><i>Gambar 2.10.6.1.7 State Awal Pop 100, Iter 3000</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter3000_seed1_final.png" width="320"><br><i>Gambar 2.10.6.1.8 State Akhir Pop 100, Iter 3000</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop100_iter3000_seed1_plot.png" width="320"><br><i>Gambar 2.10.6.1.9 Plot Nilai Objektif Pop 100, Iter 3000</i> |  |

| Iterasi | Run | Seed | Obj akhir (best) | Fee | Feasible | Gap UB | Durasi (s) |
|---|---|---|---|---|---|---|---|
| 300 | 1-3 | 1,2,3 | 721 / 863 / 858 (mean 814.0 ± 80.6) | 721 / 863 / 858 | True / True / True | 30.3% / 16.6% / 17.1% | 1.107 / 1.120 / 1.168 |
| 1000 | 1-3 | 1,2,3 | 780 / 908 / 865 (mean 851.0 ± 65.1) | 780 / 908 / 865 | True / True / True | 24.6% / 12.3% / 16.4% | 3.489 / 4.906 / 3.859 |
| 3000 | 1-3 | 1,2,3 | 803 / 927 / 876 (mean 868.7 ± 62.3) | 803 / 927 / 876 | True / True / True | 22.4% / 10.4% / 15.4% | 10.849 / 10.968 / 11.740 |

<mark>[diisi Tiara]</mark>

#### 2.10.6.2 Variasi Ukuran Populasi (Generasi Kontrol 1000)

Parameter: `population` = 50 / 100 / 200, `iterations = 1000`, `p_c = 0.8`, `p_m = 0.2`, `elitism = 2`, `epsilon = 1.0`, `selection = roulette`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Pop 50, Iter 1000** | <img src="IF3070_G09_Sepakat/output/ga/main_pop50_iter1000_seed1_initial.png" width="320"><br><i>Gambar 2.10.6.2.1 State Awal Pop 50, Iter 1000</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop50_iter1000_seed1_final.png" width="320"><br><i>Gambar 2.10.6.2.2 State Akhir Pop 50, Iter 1000</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop50_iter1000_seed1_plot.png" width="320"><br><i>Gambar 2.10.6.2.3 Plot Nilai Objektif Pop 50, Iter 1000</i> |  |
| **Pop 100, Iter 1000** | Sama dengan Gambar 2.10.6.1.4 sampai Gambar 2.10.6.1.6 pada tabel variasi banyak generasi. | <mark>[diisi Tiara]</mark> |
| **Pop 200, Iter 1000** | <img src="IF3070_G09_Sepakat/output/ga/main_pop200_iter1000_seed1_initial.png" width="320"><br><i>Gambar 2.10.6.2.4 State Awal Pop 200, Iter 1000</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop200_iter1000_seed1_final.png" width="320"><br><i>Gambar 2.10.6.2.5 State Akhir Pop 200, Iter 1000</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/ga/main_pop200_iter1000_seed1_plot.png" width="320"><br><i>Gambar 2.10.6.2.6 Plot Nilai Objektif Pop 200, Iter 1000</i> |  |

| Populasi | Run | Seed | Obj akhir (best) | Fee | Feasible | Gap UB | Durasi (s) |
|---|---|---|---|---|---|---|---|
| 50 | 1-3 | 1,2,3 | 749 / 778 / 804 (mean 777.0 ± 27.5) | 749 / 778 / 804 | True / True / True | 27.6% / 24.8% / 22.3% | 1.233 / 1.219 / 1.311 |
| 100 | 1-3 | 1,2,3 | 780 / 908 / 865 (mean 851.0 ± 65.1) | 780 / 908 / 865 | True / True / True | 24.6% / 12.3% / 16.4% | 3.489 / 4.906 / 3.859 |
| 200 | 1-3 | 1,2,3 | 860 / 940 / 826 (mean 875.3 ± 58.5) | 860 / 940 / 826 | True / True / True | 16.9% / 9.2% / 20.2% | 9.969 / 8.509 / 8.269 |

<mark>[diisi Tiara]</mark>

### 2.10.7 Multi-Kapal (Bonus 3)

Instance `src/data/multi.json` (40 kendaraan, 3 kapal, UB = 1318). Parameter: `max_iterations = 10000`, `initial_p_inside = 0.5`

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed1_initial.png" width="320"><br><i>Gambar 2.10.7.1 State Awal Trial 1</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed1_final.png" width="320"><br><i>Gambar 2.10.7.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed1_plot.png" width="320"><br><i>Gambar 2.10.7.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed2_initial.png" width="320"><br><i>Gambar 2.10.7.4 State Awal Trial 2</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed2_final.png" width="320"><br><i>Gambar 2.10.7.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed2_plot.png" width="320"><br><i>Gambar 2.10.7.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed3_initial.png" width="320"><br><i>Gambar 2.10.7.7 State Awal Trial 3</i> | <mark>[diisi Riantama]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed3_final.png" width="320"><br><i>Gambar 2.10.7.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/steepest/multi_seed3_plot.png" width="320"><br><i>Gambar 2.10.7.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj awal | Obj akhir | Fee | Feasible | Gap UB | Berat per kapal | Kendaraan per kapal | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | -59430 | 1170 | 1170 | True | 11.2% | 70/80 / 51/54 / 30/32 | 10 / 6 / 5 | 18.668 |
| 2 | 2 | -37965 | 1072 | 1072 | True | 18.7% | 63/80 / 54/54 / 26/32 | 13 / 5 / 5 | 15.176 |
| 3 | 3 | -76448 | 1078 | 1078 | True | 18.2% | 78/80 / 48/54 / 15/32 | 4 / 8 / 7 | 19.427 |
| **mean ± std** |  |  | 1106.7 ± 54.9 | 1106.7 ± 54.9 |  |  |  |  | 17.757 ± 2.267 |

<mark>[diisi Riantama]</mark>

### 2.10.8 Ringkasan Antar-Algoritma

Tabel ringkasan antar-algoritma dari `output/summary.md` (*instance* utama, 3 *run* per algoritma, UB = 1035). GA diwakili konfigurasi dengan rata-rata *objective* terbaik.

| Algoritma | Best | Mean ± std | Gap UB (mean) | Durasi mean (s) | Evaluasi mean |
|---|---|---|---|---|---|
| Steepest Ascent HC | 982 | 954.0 ± 45.1 | 7.8% | 7.331 | 229240 |
| Simulated Annealing | 973 | 966.3 ± 5.9 | 6.6% | 6.625 | 100100 |
| Stochastic HC (Bonus 2) | 876 | 808.3 ± 58.7 | 21.9% | 0.973 | 31167 |
| Sideways Move HC (Bonus 2) | 982 | 973.3 ± 11.7 | 6.0% | 48.633 | 1454799 |
| Random Restart HC (Bonus 2) | 993 | 973.7 ± 24.6 | 5.9% | 78.697 | 2534374 |
| GA, konfigurasi terbaik (pop 200, iter 1000) | 940 | 875.3 ± 58.5 | 15.4% | 8.916 | 198200 |

Gambar: `output/summary_algorithms.png` (semua algoritma), `output/summary_ga_iter.png` (GA variasi generasi), `output/summary_ga_pop.png` (GA variasi populasi).

<p align="center"><img src="IF3070_G09_Sepakat/output/summary_algorithms.png" width="560"></p>

<p align="center"><i>Gambar 2.10.8.1 Ringkasan Antar-Algoritma: Objective Akhir dan Durasi</i></p>

<p align="center"><img src="IF3070_G09_Sepakat/output/summary_ga_iter.png" width="560"></p>

<p align="center"><i>Gambar 2.10.8.2 GA Populasi 100: Objective Akhir dan Durasi per Banyak Generasi</i></p>

<p align="center"><img src="IF3070_G09_Sepakat/output/summary_ga_pop.png" width="560"></p>

<p align="center"><i>Gambar 2.10.8.3 GA 1000 Generasi: Objective Akhir dan Durasi per Ukuran Populasi</i></p>

### 2.10.9 Bonus 1: Objective Urgensi ETA

Parameter: `iterations = 100000`, `t_min = 0.01`, `t0_samples = 100`, `t0_accept = 0.8`, `stuck_window = 500`, `initial_p_inside = 0.5`. Bobot kendaraan `fee · (1 + 1/(eta + 1))`, UB bobot = 1346.25.

Tabel berikut menunjukkan ringkasan visualisasi untuk setiap percobaan:

| Trial | Visualisasi | Keterangan |
|---|---|---|
| **Trial 1** | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed1_initial.png" width="320"><br><i>Gambar 2.10.9.1 State Awal Trial 1</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed1_final.png" width="320"><br><i>Gambar 2.10.9.2 State Akhir Trial 1</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed1_plot.png" width="320"><br><i>Gambar 2.10.9.3 Plot Nilai Objektif Trial 1</i> |  |
| **Trial 2** | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed2_initial.png" width="320"><br><i>Gambar 2.10.9.4 State Awal Trial 2</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed2_final.png" width="320"><br><i>Gambar 2.10.9.5 State Akhir Trial 2</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed2_plot.png" width="320"><br><i>Gambar 2.10.9.6 Plot Nilai Objektif Trial 2</i> |  |
| **Trial 3** | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed3_initial.png" width="320"><br><i>Gambar 2.10.9.7 State Awal Trial 3</i> | <mark>[diisi Tiara]</mark> |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed3_final.png" width="320"><br><i>Gambar 2.10.9.8 State Akhir Trial 3</i> |  |
|  | <img src="IF3070_G09_Sepakat/output/sa/main_eta_seed3_plot.png" width="320"><br><i>Gambar 2.10.9.9 Plot Nilai Objektif Trial 3</i> |  |

| Run | Seed | Obj awal | Obj akhir (bobot) | Fee asli | Feasible | Gap UB | Dimuat | Berat | Iterasi | #Stuck | Durasi (s) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1 | -30496.8 | 1293.3 | 984 | True | 3.9% | 16 | 130/131 | 100000 | 175 | 1.382 |
| 2 | 2 | -72463.9 | 1223.6 | 941 | True | 9.1% | 16 | 128/131 | 100000 | 178 | 1.387 |
| 3 | 3 | -40726.8 | 1228.8 | 941 | True | 8.7% | 15 | 124/131 | 100000 | 178 | 1.427 |
| **mean ± std** |  |  | 1248.6 ± 38.8 | 955.3 ± 24.8 |  |  |  |  |  |  | 1.398 ± 0.025 |

Bobot urgensi `fee * (1 + 1/(eta + 1))`, gap terhadap UB bobot. Perbandingan dengan *run* *objective* *fee* pada *seed* yang sama: `output/summary_eta.md`.

Perbandingan dengan *run* *objective* *fee* pada *seed* yang sama (dari `output/summary_eta.md`):

| Seed | Objective | Fee asli | Bobot urgensi | Dimuat | Mean ETA dimuat | Feasible | Gap UB |
|---|---|---|---|---|---|---|---|
| 1 | fee | 964 | 1243.5 | 11 | 3.82 | True | 6.9% |
| 1 | eta | 984 | 1293.3 | 16 | 3.62 | True | 3.9% |
| 2 | fee | 973 | 1206.8 | 15 | 4.20 | True | 6.0% |
| 2 | eta | 941 | 1223.6 | 16 | 3.44 | True | 9.1% |
| 3 | fee | 962 | 1148.1 | 17 | 4.29 | True | 7.1% |
| 3 | eta | 941 | 1228.8 | 15 | 3.80 | True | 8.7% |

<mark>[diisi Tiara]</mark>

## 2.11 Analisis Hasil Eksperimen

**Kualitas hasil.** Seluruh 36 *run* menghasilkan *state* akhir yang *feasible*. Berdasarkan rata-rata *objective* akhir, urutannya adalah Random Restart HC (Bonus 2) (973.7), Sideways Move HC (Bonus 2) (973.3), Simulated Annealing (966.3), Steepest Ascent HC (954.0), GA, konfigurasi terbaik (pop 200, iter 1000) (875.3), Stochastic HC (Bonus 2) (808.3). Nilai terbaik dari satu *run* adalah 993 oleh Random Restart HC (Bonus 2). Varian HC yang mengevaluasi seluruh *neighborhood* (Steepest, Sideways, Random Restart) dan SA menghasilkan rata-rata di atas 950. GA dan Stochastic HC berada di bawahnya. Pada GA, rata-rata naik seiring bertambahnya generasi (300: 814.0 ± 80.6, 1000: 851.0 ± 65.1, 3000: 868.7 ± 62.3) dan bertambahnya populasi (50: 777.0 ± 27.5, 100: 851.0 ± 65.1, 200: 875.3 ± 58.5).

**Jarak ke *upper bound*.** Upper bound 1035 berasal dari relaksasi *knapsack* (berat dan luas) yang mengabaikan bentuk dan posisi kendaraan. Karena itu, nilai *global optimum* yang sebenarnya bisa lebih kecil dari UB, dan gap terhadap UB adalah batas atas jarak sebenarnya ke *global optimum*. Gap rata-rata berkisar dari 5.9% (Random Restart HC (Bonus 2)) sampai 21.9% (Stochastic HC (Bonus 2)), dan gap *run* terbaik adalah 4.1%. Angka ini tidak menunjukkan bahwa *global optimum* tercapai, dan juga tidak berarti hasil pasti sejauh itu dari optimum. Yang dapat disimpulkan hanyalah bahwa jarak ke *global optimum* tidak lebih dari nilai gap tersebut. Untuk multi-kapal, gap rata-rata 16.0% terhadap UB 1318; untuk Bonus 1, 7.3% terhadap UB bobot 1346.25.

**Durasi.** Pada *run* resmi, rata-rata durasi tercepat adalah Stochastic HC (Bonus 2) (0.973 s) dan terlama Random Restart HC (Bonus 2) (78.697 s). Durasi terutama mengikuti banyaknya evaluasi *objective*: Random Restart dan Sideways mengevaluasi jauh lebih banyak *neighbor* (2534374 dan 1454799 evaluasi rata-rata) dibanding SA (100100) dan Stochastic (31167).

Durasi SA *objective* *fee* pada *run* resmi (6.625 s) tampak janggal bila dibandingkan dengan SA Bonus 1, yang memakai 100 000 iterasi yang sama tetapi hanya 1.398 s. Run Bonus 1 dijalankan terpisah pada kondisi mesin yang berbeda, jadi keduanya tidak bisa dibandingkan langsung. Untuk memeriksanya, SA serta dua varian HC sebagai pembanding dijalankan ulang pada Kamis, 22 Oktober, ke folder sementara. Objective akhir dan *state* akhir hasil ukur ulang identik dengan *run* resmi.

| Algoritma | Durasi resmi (s), seed 1 / 2 / 3 | Mean resmi (s) | Durasi ukur ulang (s), seed 1 / 2 / 3 | Mean ukur ulang (s) | Resmi ÷ ukur ulang |
|---|---|---|---|---|---|
| Simulated Annealing | 7.037 / 6.651 / 6.186 | 6.625 | 2.359 / 2.353 / 2.471 | 2.394 | 2.8× |
| Steepest Ascent HC | 5.628 / 9.368 / 6.997 | 7.331 | 3.964 / 3.446 / 2.720 | 3.377 | 2.2× |
| Stochastic HC (Bonus 2) | 0.850 / 0.854 / 1.214 | 0.973 | 0.717 / 0.667 / 0.667 | 0.684 | 1.4× |

Semua algoritma yang diukur ulang ternyata lebih cepat, dengan selisih yang tidak seragam. Jadi, durasi *run* resmi (Rabu, 21 Oktober, laptop berdaya baterai) kemungkinan terpengaruh beban laptop saat *run*, dan SA yang paling terpengaruh. Durasi pada tabel ringkasan sebaiknya dibaca sebagai urutan kasar antar-algoritma, bukan angka pasti. Durasi per evaluasi juga tidak dibandingkan antar-algoritma karena alasan yang sama.

**Konsistensi.** Simpangan baku *objective* akhir antar-seed terkecil dimiliki Simulated Annealing (±5.9) dan terbesar Stochastic HC (Bonus 2) (±58.7). Urutan lengkap dari yang paling konsisten: Simulated Annealing (±5.9), Sideways Move HC (Bonus 2) (±11.7), Random Restart HC (Bonus 2) (±24.6), Steepest Ascent HC (±45.1), GA, konfigurasi terbaik (pop 200, iter 1000) (±58.5), Stochastic HC (Bonus 2) (±58.7). Dengan hanya tiga *seed* per algoritma, simpangan baku ini masih kasar dan sebaiknya dibaca sebagai indikasi, bukan kesimpulan statistik.

# Bab 3 Kesimpulan dan Saran

## 3.1 Kesimpulan

1. Keenam algoritma (Steepest Ascent, Stochastic, Sideways Move, Random Restart, Simulated Annealing, dan Genetic Algorithm) berhasil menghasilkan penataan yang memenuhi semua constraint pada ketiga *seed*. Objective dengan *penalty* dapat mendorong *state* awal yang tidak *feasible* menjadi *state* akhir yang *feasible*.
2. Pada *instance* utama, rata-rata *objective* akhir tertinggi dicapai Random Restart HC (Bonus 2) (973.7) dan Sideways Move HC (Bonus 2) (973.3), dengan durasi jauh lebih lama dibanding Steepest Ascent dan SA. SA memberi hasil yang paling konsisten antar-seed (±5.9) dengan durasi rata-rata 6.625 s.
3. Gap terhadap *upper bound* pada *run* terbaik adalah 4.1%. Karena UB berasal dari relaksasi yang mengabaikan geometri, jarak sebenarnya ke *global optimum* paling besar sebesar nilai tersebut.
4. Pada GA, menambah generasi maupun ukuran populasi meningkatkan rata-rata *objective* akhir, tetapi hasil GA pada konfigurasi yang diuji masih di bawah varian HC berbasis *neighborhood* penuh dan SA. <mark>[diisi Tiara]</mark> lengkapi alasannya.
5. Bonus 3: Steepest Ascent pada tiga kapal menghasilkan rata-rata 1106.7 (gap rata-rata 16.0%). <mark>[diisi Riantama]</mark> lengkapi analisisnya. Bonus 1: *objective* urgensi ETA memuat kendaraan dengan ETA rata-rata lebih kecil dibanding *objective* *fee* pada ketiga *seed* (`output/summary_eta.md`). <mark>[diisi Tiara]</mark> lengkapi analisisnya.
6. <mark>[diisi Riantama]</mark> Kesimpulan tentang perilaku Hill-Climbing: *local optimum*, *shoulder* dan *plateau* pada Sideways, serta manfaat *restart*.
7. <mark>[diisi Tiara]</mark> Kesimpulan tentang SA (pengaruh T0 dan *cooling*, frekuensi *stuck*) dan GA (roulette, *crossover*, mutasi, *elitism*).

## 3.2 Saran

1. Menjalankan lebih banyak *seed* (misalnya 10) supaya perbandingan konsistensi antar-algoritma lebih kuat secara statistik.
2. Mengukur durasi pada kondisi mesin yang terkontrol (daya listrik tersambung, tanpa aplikasi lain). Pada ukur ulang, durasi SA turun dari 6.625 s menjadi 2.394 s dengan hasil yang identik.
3. Membandingkan algoritma pada jumlah evaluasi yang sama, bukan hanya pada parameter *default* masing-masing.
4. Mencari *upper bound* yang lebih ketat (misalnya memperhitungkan bentuk kendaraan), atau menerapkan *brute force* pada *instance* yang sedikit lebih besar, supaya gap lebih mendekati jarak sebenarnya ke *global optimum*.
5. <mark>[diisi Riantama]</mark> Saran untuk Hill-Climbing dan multi-kapal.
6. <mark>[diisi Tiara]</mark> Saran untuk SA, GA, dan *objective* ETA (misalnya variasi `p_c`, `p_m`, atau jadwal pendinginan lain).

# Referensi

Dari komentar sumber di kode (hanya satu: docstring `src/search/hill_climbing.py`, baris 3–4):

Khodra, M. L. (2021). *Beyond Classical Search: Hill-climbing Search* [Video]. YouTube. https://www.youtube.com/watch?v=L0b0CN3Fds8

Dokumentasi library dan alat yang dipakai:

Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90–95. https://doi.org/10.1109/MCSE.2007.55

The Matplotlib Development Team. (2025). *Matplotlib 3.10.8 documentation*. Matplotlib. https://matplotlib.org/3.10.8/

Python Software Foundation. (2026). *The Python Standard Library (Python 3.14)*. Python Documentation. https://docs.python.org/3.14/library/index.html

Python Software Foundation. (2026). *argparse — Parser for command-line options, arguments and subcommands*. Python Documentation. https://docs.python.org/3.14/library/argparse.html

Python Software Foundation. (2026). *unittest — Unit testing framework*. Python Documentation. https://docs.python.org/3.14/library/unittest.html

Project Jupyter. (2026). *Jupyter Notebook 7.6.3 documentation*. Project Jupyter. https://jupyter-notebook.readthedocs.io/en/v7.6.3/

Referensi spesifikasi yang relevan untuk bab algoritma (tidak tercantum sebagai komentar di kode, tambahkan bila dipakai oleh Riantama / Tiara):

Khodra, M. L. (2021). *Beyond Classical Search: Simulated Annealing* [Video]. YouTube. https://www.youtube.com/watch?v=AdhG7HnhYrk

Khodra, M. L. (2021). *Beyond Classical Search: Genetic Algorithm* [Video]. YouTube. https://www.youtube.com/watch?v=aI41TGo9J9c
