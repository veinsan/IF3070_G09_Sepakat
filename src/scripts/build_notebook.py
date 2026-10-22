"""Bangun notebook analisis resmi; --execute menjalankannya setelah semua artefak tersedia.

Pola sel mengikuti ref/notebook/build_template.py. Eksekusi memakai API resmi
https://nbclient.readthedocs.io/en/latest/client.html, tanpa instalasi jaringan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "notebooks" / "experiments.ipynb"
HR = "---"
cells = []


def md(source: str) -> dict:
    identity = hashlib.sha256((str(len(cells)) + source).encode()).hexdigest()[:12]
    return {"cell_type": "markdown", "id": identity, "metadata": {}, "source": source}


def code(source: str) -> dict:
    cell = md(source)
    return {**cell, "cell_type": "code", "execution_count": None, "outputs": []}


def section(title: str, anchor: str) -> dict:
    return md(f'{HR}\n\n# {title} <a name="{anchor}"></a>\n\n{HR}')


cells.append(md(
    '---\n'
    '\n'
    '# Sepakat: Optimasi Muatan Kapal\n'
    '\n'
    '*Analisis eksperimen local search pada penataan kendaraan, kapasitas berat, dan pendapatan pengiriman.*'
))

cells.append(md(
    '---\n'
    '\n'
    '## G09 - Sepakat\n'
    '\n'
    '- Riantama Putra (18224061)\n'
    '- Tiara Kusuma Wardhani (18224059)\n'
    '- Levina Nathania Bunardi (18224057)'
))

cells.append(md(
    '---\n'
    '\n'
    '## Daftar Isi\n'
    '\n'
    '1. [Introduction](#1)\n'
    '2. [Initialization](#2)\n'
    '3. [Data dan Protokol](#3)\n'
    '4. [Tabel Eksperimen](#4)\n'
    '5. [Hill-Climbing](#5)\n'
    '6. [Simulated Annealing](#6)\n'
    '7. [Genetic Algorithm](#7)\n'
    '8. [Perbandingan Algoritma](#8)\n'
    '9. [State Terbaik](#9)\n'
    '10. [Multi-kapal dan ETA](#10)\n'
    '11. [Batas Atas dan Optimum Eksak](#11)\n'
    '12. [Kesimpulan dan Referensi](#12)'
))

cells.append(section('Introduction', '1'))

cells.append(md(
    '## Overview\n'
    '\n'
    '*Notebook ini membaca hasil resmi dari `output/experiments/` tanpa mengulang pencarian. Semua angka, tabel, dan simpulan kuantitatif dihitung dari JSON saat notebook dijalankan; sel analisis berhenti jika artefak belum lengkap.*\n'
    '\n'
    '*Hill-Climbing memilih tetangga yang memperbaiki objective, dengan varian stochastic, sideways, dan random restart. Simulated Annealing dapat menerima penurunan dengan peluang `exp(delta/T)`. Genetic Algorithm menggunakan seleksi roulette, crossover satu titik, mutasi, dan elitisme pada populasi.*\n'
    '\n'
    '*Objective pendapatan dikurangi penalti pelanggaran. State awal tetap acak dan boleh tidak feasible; state akhir merupakan incumbent feasible terbaik yang tercatat, termasuk baseline kapal kosong bila belum ditemukan kandidat feasible. Nilai maksimum populasi atau state berjalan tidak selalu sama dengan incumbent ini. Batas atas relaksasi bukan bukti optimum geometris.*'
))

cells.append(section('Initialization', '2'))

cells.append(md(
    '## Environment Setup\n'
    '\n'
    'Analisis dan algoritma berjalan pada CPU, tanpa GPU atau unduhan otomatis. Dari root repository, siapkan lingkungan dengan `python -m pip install -r requirements.txt`, lalu jalankan `python src/experiments.py` untuk menghasilkan seluruh eksperimen resmi. Notebook dapat dibuka dari root atau direktori `notebooks/`.\n'
    '\n'
    'Pembangun `python src/scripts/build_notebook.py` menghasilkan notebook bersih. Opsi `--execute` menjalankannya melalui kernel Python lokal setelah artefak lengkap; eksekusi notebook tidak memasang paket melalui jaringan.'
))

cells.append(md(
    '## Import Libraries\n'
    '\n'
    'Sel Libraries memusatkan seluruh impor dan menambahkan `src/` ke jalur modul lokal sebelum memuat kode proyek.'
))

cells.append(code(
    'import math\n'
    'import random\n'
    'import sys\n'
    'from collections import Counter\n'
    'from io import BytesIO\n'
    'from pathlib import Path\n'
    'from statistics import mean, stdev\n'
    '\n'
    'import matplotlib.pyplot as plt\n'
    'from matplotlib.figure import Figure\n'
    'from IPython.display import Image, Markdown, display\n'
    '\n'
    "ROOT = next((p for p in (Path.cwd(), *Path.cwd().parents) if (p / 'src' / 'experiments.py').is_file()), None)\n"
    'if ROOT is None:\n'
    "    raise FileNotFoundError('Buka notebook dari dalam repository Sepakat.')\n"
    "sys.path.insert(0, str(ROOT / 'src'))\n"
    'from config import DATA_DIR, EXPERIMENTS_DIR\n'
    'from core.bounds import brute_force, upper_bound\n'
    'from core.eta_objective import eta_problem, shipping_fee_total, urgency_weight\n'
    'from core.problem import load_problem\n'
    'from core.state import State\n'
    'from experiments import comparison_groups, load_results, machine_info, planned_runs, summary_sections\n'
    'from visualization.plots import plot_objective, plot_run, plot_summary\n'
    'from visualization.state_view import draw_state'
))

cells.append(md(
    '## Seed Everything\n'
    '\n'
    'Seed analisis ditetapkan agar pemilihan tambahan tetap dapat direproduksi. Seed pencarian tetap mengikuti masing-masing JSON dan tidak diubah oleh notebook.'
))

cells.append(code(
    'def seed_everything(seed=42):\n'
    '    random.seed(seed)\n'
    '\n'
    'seed_everything(42)'
))

cells.append(md(
    '## Settings\n'
    '\n'
    'Lokasi data dan hasil memakai konfigurasi proyek. Tampilan grafik memakai ukuran terbaca dan palet yang konsisten; notebook tidak menulis ulang hasil pencarian.'
))

cells.append(code(
    'class Settings:\n'
    '    SEED = 42\n'
    '    DATA_DIR = DATA_DIR\n'
    '    OUT = EXPERIMENTS_DIR\n'
    '    EXPECTED_RUNS = 39\n'
    '    EXPECTED_REQUIRED = 24\n'
    '    EXACT_MAX_NODES = 5_000_000\n'
    "    COLORS = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9']\n"
    '\n'
    'CFG = Settings()\n'
    "plt.rcParams.update({'font.size': 9, 'axes.grid': True, 'grid.alpha': 0.2,\n"
    "                     'axes.prop_cycle': plt.cycler(color=CFG.COLORS), 'figure.dpi': 100})\n"
    "print('Mesin analisis saat ini:', machine_info())\n"
    "print('Durasi dalam JSON adalah durasi pencarian, bukan waktu menggambar atau analisis.')\n"
    "print('Identitas mesin pembuat JSON tidak disimpulkan dari mesin analisis ini.')"
))

cells.append(md(
    '## Load Dataset\n'
    '\n'
    'Rencana resmi menentukan berkas yang dibaca, bukan pencarian glob yang dapat mencampurkan run manual atau quick. Setiap grup GA harus memuat sembilan eksekusi tersendiri, termasuk kontrol yang dicatat terpisah.'
))

cells.append(code(
    'plan = planned_runs()\n'
    'assert len(plan) == CFG.EXPECTED_RUNS\n'
    'assert sum(run.required for run in plan) == CFG.EXPECTED_REQUIRED\n'
    'assert all(len(run.groups) == 1 for run in plan)\n'
    'assert len({run.path(CFG.OUT) for run in plan}) == len(plan)\n'
    "for group in ('ga_iter', 'ga_pop'):\n"
    '    assert sum(run.groups[0] == group for run in plan) == 9\n'
    'missing = []\n'
    'for run in plan:\n'
    '    path = run.path(CFG.OUT)\n'
    "    for artifact in [path, *(path.with_name(path.stem + suffix) for suffix in ('_initial.png', '_final.png', '_plot.png'))]:\n"
    '        if not artifact.is_file():\n'
    '            missing.append(str(artifact.relative_to(ROOT)))\n'
    'if missing:\n'
    "    raise FileNotFoundError('Artefak belum lengkap. Jalankan python src/experiments.py.\\n' + '\\n'.join(missing))\n"
    'pairs = load_results(plan, CFG.OUT)\n'
    'assert len(pairs) == len(plan)\n'
    'problems = {run.instance: load_problem(run.instance) for run in plan}\n'
    '\n'
    'def of(group, algorithm=None):\n'
    '    return [(run, result) for run, result in pairs\n'
    '            if run.groups[0] == group and (algorithm is None or run.algo == algorithm)]\n'
    '\n'
    'def table(headers, rows):\n'
    '    def cell(value):\n'
    "        return str(value).replace('|', '/')\n"
    "    display(Markdown(' | '.join(headers) + '\\n' + ' | '.join(['---'] * len(headers)) + '\\n' +\n"
    "                     '\\n'.join(' | '.join(cell(v) for v in row) for row in rows)))\n"
    '\n'
    'def insights(text):\n'
    "    display(Markdown('#### Insights\\n\\n> ' + text))\n"
    '\n'
    'def show(fig):\n'
    '    with BytesIO() as buffer:\n'
    "        fig.savefig(buffer, format='png', dpi=110)\n"
    '        display(Image(data=buffer.getvalue()))\n'
    '    plt.close(fig)\n'
    '\n'
    "print(f'{len(pairs)} run lengkap; {sum(run.required for run in plan)} wajib.')"
))

cells.append(section('Data dan Protokol', '3'))

cells.append(md(
    'Setiap state awal dan akhir direkonstruksi dari penempatan kendaraan pada instance yang tepat. Pemeriksaan ini menghitung ulang objective, feasibility, fee, dan batas atas, serta memastikan berkas PNG dapat dibaca sebelum analisis dilanjutkan.'
))

cells.append(code(
    'audit = []\n'
    'for run, result in pairs:\n'
    '    original = problems[run.instance]\n'
    "    problem = eta_problem(original) if run.objective == 'eta' else original\n"
    "    assert result['algorithm'] == run.algo and result['seed'] == run.seed\n"
    "    assert result['instance'] == problem.name\n"
    "    assert result.get('extra', {}).get('objective', 'fee') == run.objective\n"
    '    for key, value in run.params.items():\n'
    "        assert result['params'][key] == value\n"
    "    for key in ('initial', 'final'):\n"
    "        state = State.from_dict(problem, result[key + '_state'])\n"
    '        evaluation = state.evaluate()\n'
    "        assert math.isclose(evaluation.objective, result[key + '_objective'], abs_tol=1e-7)\n"
    "        if key == 'final':\n"
    "            assert evaluation.is_feasible and result['is_feasible']\n"
    "            assert math.isclose(evaluation.total_fee, result['total_fee'], abs_tol=1e-7)\n"
    "            if run.objective == 'eta':\n"
    '                assert math.isclose(shipping_fee_total(original, state.positions),\n'
    "                                    result['extra']['shipping_fee_total'], abs_tol=1e-7)\n"
    '    bound = upper_bound(problem)\n'
    "    assert math.isclose(bound, result['upper_bound'], abs_tol=1e-7)\n"
    "    assert result['final_objective'] <= bound + 1e-7\n"
    '    if bound:\n'
    "        assert math.isclose((bound - result['final_objective']) / bound, result['gap_ub'], abs_tol=1e-7)\n"
    '    path = run.path(CFG.OUT)\n'
    "    for suffix in ('_initial.png', '_final.png', '_plot.png'):\n"
    '        assert plt.imread(path.with_name(path.stem + suffix)).size > 0\n'
    "    audit.append([run.groups[0], run.algo, run.seed, result['final_objective'],\n"
    "                  result['extra'].get('empty_baseline_used', False)])\n"
    "table(['Instance', 'Kapal', 'Kendaraan', 'Luas geladak', 'Kapasitas berat'],\n"
    '      [[p.name, len(p.ships), len(p.vehicles), sum(s.area for s in p.ships),\n'
    '        sum(s.max_capacity for s in p.ships)] for p in problems.values()])\n'
    "table(['Grup', 'Run'], sorted(Counter(row[0] for row in audit).items()))\n"
    "insights(f'Seluruh {len(audit)} state akhir lolos evaluasi ulang; '\n"
    "         f'{sum(row[4] for row in audit)} run memakai baseline kosong. '\n"
    "         'Feasibility sendiri tidak membuktikan pencarian menemukan muatan yang berguna.')"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Tiap sweep GA memiliki run tersendiri. Kontrol dengan seed dan parameter identik bukan sampel acak baru untuk perbandingan antar-algoritma; fungsi `comparison_groups` menghindari penghitungan ganda.'
))

cells.append(section('Tabel Eksperimen', '4'))

cells.append(md(
    'Tabel resmi memakai helper yang sama dengan runner agar jumlah iterasi, parameter, durasi, restart, sideways, stuck, dan hasil setiap seed tetap konsisten. Nilai bobot ETA dan pendapatan asli ditampilkan terpisah.'
))

cells.append(code(
    "display(Markdown('\\n'.join(summary_sections(pairs))))"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Mean dan simpangan baku merangkum tiga seed, bukan jaminan statistik untuk semua instance. Gap UB membandingkan solusi dengan relaksasi yang mengabaikan geometri dan tidak boleh disebut gap optimum eksak.'
))

cells.append(section('Hill-Climbing', '5'))

cells.append(md(
    'Kurva menampilkan objective berjalan setiap seed untuk seluruh varian Hill-Climbing. Garis incumbent feasible ditampilkan jika berbeda, sehingga hasil akhir tetap dapat dijelaskan meskipun pencarian berhenti pada state berpenalti; nilai negatif tidak dipotong.'
))

cells.append(code(
    "hc_pairs = of('hc') + of('hc_variants')\n"
    "fig = Figure(figsize=(15, 12), layout='constrained')\n"
    'axes = fig.subplots(4, 3).flat\n'
    'for ax, (run, result) in zip(axes, hc_pairs):\n'
    '    plot_objective(ax, result)\n'
    '    ax.set_title(f"{run.algo}, seed {run.seed}: {result[\'iterations\']} iterasi", fontsize=9)\n'
    'show(fig)\n'
    "hc_means = {algo: mean(r['final_objective'] for run, r in hc_pairs if run.algo == algo)\n"
    '            for algo in sorted({run.algo for run, r in hc_pairs})}\n'
    "insights('Rata-rata objective akhir: ' + '; '.join(f'{a} = {v:.2f}' for a, v in hc_means.items()) +\n"
    "         '. Selisih ini merupakan pengamatan pada seed dan batas iterasi yang dicatat, bukan bukti satu varian selalu unggul.')"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Steepest memeriksa banyak tetangga per langkah; satu iterasi tidak setara dengan satu evaluasi. Random restart mempunyai garis terbaik lintas percobaan, sedangkan sideways dan stochastic dibatasi parameter penghentian masing-masing pada tabel.'
))

cells.append(section('Simulated Annealing', '6'))

cells.append(md(
    'SA dapat menurunkan objective berjalan ketika menerima langkah memburuk. Setiap panel peluang hanya menampilkan iterasi dengan delta negatif yang benar-benar tercatat; incumbent feasible tetap menjadi dasar hasil akhir.'
))

cells.append(code(
    "for run, result in of('sa'):\n"
    '    show(plot_run(result))'
))

cells.append(code(
    "sa_results = [result for run, result in of('sa')]\n"
    "table(['Seed', 'Episode stuck teramati', 'Stagnation', 'Checkpoint', 'Evaluasi', 'Objective akhir'],\n"
    "      [[r['seed'], r['extra'].get('stuck_count', 'tidak dicatat'),\n"
    "        r['extra'].get('stagnation_count', 'tidak dicatat'), r['params'].get('stuck_window', 'lihat JSON'),\n"
    "        r['evaluations'], r['final_objective']] for r in sa_results])\n"
    'insights(f"Rata-rata episode stuck teramati = {mean(r[\'extra\'][\'stuck_count\'] for r in sa_results):.2f}; "\n'
    '         f"rata-rata objective akhir = {mean(r[\'final_objective\'] for r in sa_results):.2f}. "\n'
    "         'Episode dihitung dari pemeriksaan tetangga pada checkpoint, bukan dari setiap langkah tanpa perbaikan. '\n"
    "         'Checkpoint dengan tetangga membaik memutus rangkaian episode; stagnasi dicatat terpisah.')"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Kurva peluang menggambarkan mekanisme penerimaan, bukan persentase keberhasilan pencarian. Episode stuck yang tidak teramati di antara checkpoint tidak dapat dihitung dari ringkasan ini; evaluasi pemeriksaan tetangga termasuk biaya pencarian.'
))

cells.append(section('Genetic Algorithm', '7'))

cells.append(md(
    'Dua sweep dilakukan terpisah, masing-masing tiga konfigurasi dan tiga seed. Tiap panel memperlihatkan maksimum dan rata-rata populasi serta incumbent feasible jika berbeda; maksimum populasi yang belum feasible bukan solusi muatan yang dapat dikirim.'
))

cells.append(code(
    "for group in ('ga_iter', 'ga_pop'):\n"
    "    fig = Figure(figsize=(15, 10), layout='constrained')\n"
    '    fig.suptitle(group)\n'
    '    for ax, (run, result) in zip(fig.subplots(3, 3).flat, of(group)):\n'
    '        plot_objective(ax, result)\n'
    '        ax.set_title(f"pop {result[\'params\'][\'population\']}, iter {result[\'params\'][\'iterations\']}, seed {run.seed}", fontsize=9)\n'
    '    show(fig)'
))

cells.append(code(
    'ga_budget_rows = []\n'
    "for group, key in (('ga_iter', 'iterations'), ('ga_pop', 'population')):\n"
    '    members = of(group)\n'
    "    for value in sorted({r['params'][key] for run, r in members}):\n"
    "        selected = [r for run, r in members if r['params'][key] == value]\n"
    "        ga_budget_rows.append([group, value, mean(r['final_objective'] for r in selected),\n"
    "                               stdev(r['final_objective'] for r in selected),\n"
    "                               mean(r['duration_s'] for r in selected), mean(r['evaluations'] for r in selected)])\n"
    "table(['Sweep', 'Nilai parameter', 'Obj mean', 'Obj std', 'Durasi mean (s)', 'Evaluasi mean'],\n"
    "      [[*row[:2], *(f'{v:.3f}' for v in row[2:])] for row in ga_budget_rows])\n"
    "for group in ('ga_iter', 'ga_pop'):\n"
    '    rows = [row for row in ga_budget_rows if row[0] == group]\n'
    '    low, high = rows[0], rows[-1]\n'
    "    insights(f'{group}: dari {low[1]} ke {high[1]}, perubahan mean objective = {high[2] - low[2]:+.2f}, '\n"
    "             f'durasi = {high[4] - low[4]:+.3f} s, evaluasi = {high[5] - low[5]:+.0f}. '\n"
    "             'Angka ini membandingkan budget aktual pada sweep tersebut; tidak menyatakan hubungan kausal universal.')"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Populasi dan generasi sama-sama memengaruhi jumlah evaluasi, sehingga kualitas perlu dibaca bersama biaya aktual. Kenaikan parameter tidak otomatis menjamin kenaikan kualitas pada setiap seed; kontrol kedua sweep tetap tersimpan terpisah.'
))

cells.append(section('Perbandingan Algoritma', '8'))

cells.append(md(
    'Perbandingan hanya mencakup objective fee pada instance utama. GA diwakili konfigurasi dengan mean terbaik yang dipilih dari sweep yang sama; pemilihan ini bersifat deskriptif dan berpotensi optimistis, bukan evaluasi pada data uji terpisah.'
))

cells.append(code(
    'compare = comparison_groups(pairs)\n'
    'comparison = []\n'
    'for label, results in compare.items():\n'
    "    finals = [r['final_objective'] for r in results]\n"
    '    comparison.append([label, len(results), max(finals), mean(finals), stdev(finals) if len(finals) > 1 else 0,\n'
    "                       mean(r['duration_s'] for r in results), mean(r['evaluations'] for r in results),\n"
    "                       100 * mean(r['gap_ub'] for r in results)])\n"
    "table(['Algoritma', 'n', 'Best', 'Mean', 'Std', 'Durasi (s)', 'Evaluasi', 'Gap UB (%)'],\n"
    "      [[row[0], row[1], *(f'{v:.3f}' for v in row[2:])] for row in comparison])\n"
    'labels = {id(r): label for label, results in compare.items() for r in results}\n'
    'show(plot_summary([r for results in compare.values() for r in results], group=lambda r: labels[id(r)]))\n'
    'best_quality = max(comparison, key=lambda row: row[3])\n'
    'fastest = min(comparison, key=lambda row: row[5])\n'
    'consistent = min(comparison, key=lambda row: row[4])\n'
    "insights(f'Mean kualitas tertinggi: {best_quality[0]} ({best_quality[3]:.2f}); '\n"
    "         f'durasi mean terendah: {fastest[0]} ({fastest[5]:.3f} s); '\n"
    "         f'simpangan baku terendah: {consistent[0]} ({consistent[4]:.2f}). '\n"
    "         'Jika terjadi seri, urutan tabel menentukan nama yang ditampilkan. '\n"
    "         'Variansi kecil pada nilai rendah tidak berarti solusi berkualitas tinggi.')"
))

cells.append(md(
    '## Biaya Evaluasi Aktual\n'
    '\n'
    'Sumbu biaya menggunakan penghitung kumulatif `history.evaluations`, bukan interpolasi dari total evaluasi. Garis bertangga menahan incumbent pada evaluasi terakhir yang tercatat, tanpa mengarang peningkatan di antara dua observasi.'
))

cells.append(code(
    "fig = Figure(figsize=(10, 4), layout='constrained')\n"
    'ax = fig.subplots()\n'
    'omitted = []\n'
    'for label, results in compare.items():\n'
    "    result = max(results, key=lambda r: r['final_objective'])\n"
    "    history = result['history']\n"
    "    x = history.get('evaluations')\n"
    "    y = history.get('best_feasible')\n"
    '    if x is None or y is None or len(x) != len(y):\n'
    '        omitted.append(label)\n'
    '        continue\n'
    '    assert all(b >= a for a, b in zip(x, x[1:]))\n'
    "    assert x[-1] <= result['evaluations']\n"
    '    ax.step(x, y, where=\'post\', label=f"{label}, seed {result[\'seed\']}")\n'
    "ax.set(xlabel='evaluasi kumulatif tercatat', ylabel='incumbent feasible', title='Run terbaik per algoritma, tanpa interpolasi')\n"
    'if ax.lines:\n'
    '    ax.legend(fontsize=7)\n'
    '    show(fig)\n'
    'else:\n'
    "    print('Kurva evaluasi dihilangkan: tidak ada history evaluasi yang selaras.')\n"
    'if omitted:\n'
    "    print('Kurva dihilangkan karena history evaluasi/incumbent tidak tersedia atau tidak selaras:', ', '.join(omitted))"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Ranking kualitas, kecepatan, dan konsistensi menjawab pertanyaan berbeda. Plot biaya memakai satu run terbaik per algoritma untuk demo, sedangkan tabel tetap merangkum semua seed; biaya evaluasi juga tidak identik dengan waktu CPU per evaluasi.'
))

cells.append(section('State Terbaik', '9'))

cells.append(md(
    'Untuk setiap algoritma pada perbandingan, state awal dan akhir dari run dengan objective akhir tertinggi digambar langsung dari JSON. Pemilihan memakai nilai akhir, bukan maksimum kurva yang mungkin masih melanggar kendala.'
))

cells.append(code(
    'for label, results in compare.items():\n'
    "    best = max(results, key=lambda r: r['final_objective'])\n"
    '    run = next(run for run, result in pairs if result is best)\n'
    '    problem = problems[run.instance]\n'
    "    for key, title in (('initial_state', 'Awal'), ('final_state', 'Akhir')):\n"
    '        show(draw_state(problem, best[key], title=f"{title}: {label}, seed {best[\'seed\']}"))\n'
    "    print(label, '| baseline kosong:', best['extra'].get('empty_baseline_used', False),\n"
    "          '| kandidat feasible ditemukan:', best['extra'].get('found_feasible', 'tidak dicatat'),\n"
    "          '| objective endpoint mentah:', best['extra'].get('raw_final_objective', 'tidak dicatat'))"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Warna mengidentifikasi kendaraan secara konsisten; panel luar kapal tetap memperlihatkan kendaraan yang tidak diangkut. Arsir dan batas merah pada state awal memperlihatkan pelanggaran, bukan kerusakan gambar. Baseline kosong dinyatakan eksplisit dan tidak disamarkan sebagai keberhasilan menemukan muatan.'
))

cells.append(section('Multi-kapal dan ETA', '10'))

cells.append(md(
    '## Multi-kapal\n'
    '\n'
    'Penataan armada mengoptimalkan nilai total dengan kendala setiap kapal. Pemeriksaan berikut menampilkan penggunaan berat, luas, dan jumlah kendaraan per kapal pada run multi terbaik, tanpa menyamakan kapasitas gabungan dengan kebebasan menempatkan kendaraan di kapal mana pun.'
))

cells.append(code(
    "multi_run, multi_best = max(of('multi'), key=lambda pair: pair[1]['final_objective'])\n"
    'multi_problem = problems[multi_run.instance]\n'
    "multi_state = State.from_dict(multi_problem, multi_best['final_state'])\n"
    'evaluation = multi_state.evaluate()\n'
    "table(['Kapal', 'Kendaraan', 'Berat', 'Kapasitas', 'Sel terisi', 'Luas'],\n"
    '      [[ship.id, sum(p is not None and p[0] == i for p in multi_state.positions),\n'
    '        evaluation.used_weight[i], ship.max_capacity, evaluation.occupied_cells[i], ship.area]\n'
    '       for i, ship in enumerate(multi_problem.ships)])\n'
    "for key, title in (('initial_state', 'Awal'), ('final_state', 'Akhir')):\n"
    "    show(draw_state(multi_problem, multi_best[key], title=f'{title}: multi-kapal, seed {multi_run.seed}'))\n"
    'insights(f"Run multi terbaik memiliki objective {multi_best[\'final_objective\']:.2f}, "\n'
    '         f"memuat {multi_best[\'loaded\']} kendaraan pada {len(multi_problem.ships)} kapal. "\n'
    "         'Hasil tidak dibandingkan langsung dengan instance satu kapal karena data dan kapasitas berbeda.')"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Feasibility dihitung per kapal, bukan hanya dari berat total armada. Satu kapal dapat menyisakan ruang karena bentuk kendaraan dan kapasitas berat; gambar saja tidak membuktikan penyebab spesifik suatu ruang kosong.'
))

cells.append(md(
    '## Objective Urgensi ETA\n'
    '\n'
    'Bobot alternatif adalah `fee * (1 + 1/(eta + 1))`. Bobot ini bukan uang dan tidak mengubah kapasitas fisik. Pasangan run fee dan ETA pada seed yang sama dinilai ulang dengan kedua metrik agar perbandingan tidak mencampurkan skala objective.'
))

cells.append(code(
    'eta_rows = []\n'
    "for eta_run, eta_result in of('eta'):\n"
    '    original = problems[eta_run.instance]\n'
    "    fee_run, fee_result = next((run, result) for run, result in of('sa') if run.seed == eta_run.seed)\n"
    '    assert fee_run.instance == eta_run.instance\n'
    "    assert fee_result['params'] == eta_result['params']\n"
    "    for mode, result in (('fee', fee_result), ('eta', eta_result)):\n"
    "        state = State.from_dict(original, result['final_state'])\n"
    '        revenue = shipping_fee_total(original, state.positions)\n'
    '        urgency = sum(urgency_weight(v) for v, p in zip(original.vehicles, state.positions) if p is not None)\n'
    '        eta_rows.append([eta_run.seed, mode, revenue, urgency,\n'
    "                         sum(p is not None for p in state.positions), result['duration_s']])\n"
    "    fee_initial = State.from_dict(original, fee_result['initial_state']).positions\n"
    "    eta_initial = State.from_dict(original, eta_result['initial_state']).positions\n"
    '    assert fee_initial == eta_initial\n'
    "table(['Seed', 'Objective pencarian', 'Fee asli', 'Bobot urgensi', 'Dimuat', 'Durasi (s)'],\n"
    "      [[*row[:2], f'{row[2]:.2f}', f'{row[3]:.2f}', row[4], f'{row[5]:.3f}'] for row in eta_rows])\n"
    "fee_mean = mean(row[2] for row in eta_rows if row[1] == 'fee')\n"
    "eta_fee_mean = mean(row[2] for row in eta_rows if row[1] == 'eta')\n"
    "fee_urgency = mean(row[3] for row in eta_rows if row[1] == 'fee')\n"
    "eta_urgency = mean(row[3] for row in eta_rows if row[1] == 'eta')\n"
    "insights(f'Perubahan mean ETA terhadap fee: pendapatan asli {eta_fee_mean - fee_mean:+.2f}; '\n"
    "         f'bobot urgensi {eta_urgency - fee_urgency:+.2f}. '\n"
    "         'Seed, parameter, dan penempatan awal berpasangan; hasil tetap merupakan sampel pencarian stokastik, '\n"
    "         'bukan jaminan trade-off dengan arah yang sama pada semua instance.')"
))

cells.append(code(
    "eta_run, eta_best = max(of('eta'), key=lambda pair: pair[1]['final_objective'])\n"
    'transformed = eta_problem(problems[eta_run.instance])\n'
    'show(plot_run(eta_best))\n'
    "for key, title in (('initial_state', 'Awal'), ('final_state', 'Akhir')):\n"
    '    original_state = State.from_dict(problems[eta_run.instance], eta_best[key])\n'
    '    actual_fee = shipping_fee_total(problems[eta_run.instance], original_state.positions)\n'
    "    show(draw_state(transformed, eta_best[key], title=f'{title}: ETA, seed {eta_run.seed}',\n"
    "                    objective='eta', shipping_fee=actual_fee))"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> `total_fee` dalam JSON ETA berisi total bobot transformasi; pendapatan moneternya berada pada `extra.shipping_fee_total`. Gambar dan tabel mempertahankan perbedaan ini, termasuk ketika kedua nilai kebetulan sama.'
))

cells.append(section('Batas Atas dan Optimum Eksak', '11'))

cells.append(md(
    'Batas atas mengabaikan sebagian kendala geometri, sehingga nilainya minimal sebesar optimum feasible. Optimum eksak hanya dihitung untuk `small.json` dengan enumerasi branch-and-bound; hasil kecil tidak membuktikan optimalitas pada instance utama atau multi-kapal.'
))

cells.append(code(
    "small = load_problem(CFG.DATA_DIR / 'small.json')\n"
    'exact = brute_force(small, max_nodes=CFG.EXACT_MAX_NODES)\n'
    'small_bound = upper_bound(small)\n'
    'assert exact.evaluate().is_feasible\n'
    'assert exact.objective <= small_bound + 1e-7\n'
    "table(['Instance', 'Optimum eksak', 'Upper bound', 'Kelonggaran UB'],\n"
    '      [[small.name, exact.objective, small_bound, small_bound - exact.objective]])\n'
    "show(draw_state(small, exact.to_dict(), title='Optimum eksak pada instance kecil'))\n"
    "main_bound = next(result['upper_bound'] for run, result in of('hc'))\n"
    "best_main = max(result['final_objective'] for results in compare.values() for result in results)\n"
    "insights(f'Instance kecil: optimum eksak {exact.objective:g}, UB {small_bound:g}. '\n"
    "         f'Instance utama: incumbent terbaik {best_main:g}, UB {main_bound:g}. '\n"
    "         + ('Kesamaan incumbent dan UB membuktikan optimum pada instance utama.'\n"
    '            if math.isclose(best_main, main_bound, abs_tol=1e-7)\n'
    "            else 'Incumbent dan UB memberi interval optimum; selisihnya tidak membuktikan seberapa jauh solusi dari optimum geometris.'))"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Jika solusi feasible mencapai UB yang valid, optimalitas terbukti untuk instance dan objective tersebut. Jika belum mencapai UB, penyebabnya dapat berupa relaksasi yang longgar, pencarian yang belum optimal, atau keduanya; hasil eksperimen ini tidak memisahkan penyebab tersebut.'
))

cells.append(section('Kesimpulan dan Referensi', '12'))

cells.append(md(
    'Ringkasan akhir menghitung jawaban atas kualitas, durasi, konsistensi, budget GA, dan indikator SA dari artefak yang telah diperiksa. Semua rekomendasi dibatasi pada instance serta seed dalam protokol ini.'
))

cells.append(code(
    'insights(f"Pada {len(pairs)} run resmi, mean kualitas tertinggi pada perbandingan adalah {best_quality[0]}; "\n'
    '         f"durasi mean terendah adalah {fastest[0]}; simpangan baku terendah adalah {consistent[0]}. "\n'
    '         f"Rata-rata episode stuck checkpoint SA adalah {mean(r[\'extra\'][\'stuck_count\'] for r in sa_results):.2f}. "\n'
    "         'Tabel GA menunjukkan biaya evaluasi dan perubahan kualitas untuk kedua sumbu budget. '\n"
    "         'Pernyataan ini merangkum pengamatan, bukan klaim dominasi algoritma secara umum.')"
))

cells.append(md(
    '#### Insights\n'
    '\n'
    '> Reproduksi analisis memerlukan data, konfigurasi, seluruh JSON, dan gambar dari run resmi yang sama. Pengulangan analisis tidak mengulangi search; perubahan algoritma atau parameter memerlukan regenerasi eksperimen sebelum simpulan baru diambil.\n'
    '\n'
    '## Referensi\n'
    '\n'
    'Spesifikasi: `docs/Spesifikasi Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026_2027.md`, bagian Cakupan dan Bonus. Implementasi dan protokol: `docs/DESIGN.md`, `docs/EXPERIMENTS.md`, serta `src/search/` dan `src/core/`.\n'
    '\n'
    'Materi IF3070 oleh M. L. Khodra: [Hill-Climbing](https://www.youtube.com/watch?v=L0b0CN3Fds8), [Simulated Annealing](https://www.youtube.com/watch?v=AdhG7HnhYrk), dan [Genetic Algorithm](https://www.youtube.com/watch?v=aI41TGo9J9c). Referensi materi lengkap mengikuti dokumen spesifikasi; kode analisis menggunakan implementasi lokal repository.'
))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Jalankan notebook setelah artefak resmi lengkap")
    args = parser.parse_args(argv)
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(cells)} cells -> {OUT}")
    if args.execute:
        import nbformat
        from nbclient import NotebookClient

        executed = nbformat.from_dict(notebook)
        client = NotebookClient(executed, timeout=600, kernel_name="python3",
                                resources={"metadata": {"path": str(ROOT)}})
        client.execute()
        nbformat.write(executed, OUT)
        print(f"Executed {len(cells)} cells -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
