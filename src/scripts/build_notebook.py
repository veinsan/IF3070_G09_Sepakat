"""Bangun notebook CARGO beserta analisis dan gambar dari eksperimen resmi.

    python src/scripts/build_notebook.py
    python src/scripts/build_notebook.py --execute

Eksekusi menggunakan API https://nbclient.readthedocs.io/en/latest/client.html.
Builder, notebook, dan gambar tidak memerlukan berkas template eksternal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "notebooks" / "experiments.ipynb"
HR = '<hr style="border: 2px solid #8E7B6B; margin-top: 10px;">'
cells: list[dict] = []


def md(source: str) -> dict:
    if source.startswith("## "):
        source = "---\n\n" + source
    identity = hashlib.sha256((str(len(cells)) + source).encode()).hexdigest()[:12]
    return {"cell_type": "markdown", "id": identity, "metadata": {}, "source": source}


def code(source: str) -> dict:
    cell = md(source)
    return {**cell, "cell_type": "code", "execution_count": None, "outputs": []}


def section(title: str, anchor: str) -> dict:
    return md(f'{HR}\n\n# {title} <a name="{anchor}"></a>\n\n{HR}')


cells.append(md(
    f'{HR}\n<br>\n'
    '<h1 style="font-family:verdana; font-size:26px"><center>~ IF3070: Optimasi Muatan Kendaraan pada Kapal ~</center></h1>\n'
    '<h3 style="font-family:verdana; font-size:14px; color:gray"><center>Constraint-Aware Revenue and Geometric Optimization</center></h3>\n'
    f'{HR}\n\n'
    '# **CARGO**'
))
cells.append(md(
    f'{HR}\n\n'
    '## Kelompok G09 - Sepakat\n\n'
    '- **Riantama Putra** - 18224061\n'
    '- **Tiara Kusuma Wardhani** - 18224059\n'
    '- **Levina Nathania Bunardi** - 18224057\n\n'
    'Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027.'
))
cells.append(md(
    f'{HR}\n\n# Daftar Isi\n\n'
    '1. [**Pendahuluan**](#1)\n'
    '2. [**Inisialisasi**](#2)\n'
    '3. [**Analisis Data Eksploratif**](#3)\n'
    '4. [**Protokol dan Hasil Eksperimen**](#4)\n'
    '5. [**Hill-Climbing**](#5)\n'
    '6. [**Simulated Annealing**](#6)\n'
    '7. [**Genetic Algorithm**](#7)\n'
    '8. [**Perbandingan Algoritma**](#8)\n'
    '9. [**Visualisasi Penataan Kendaraan**](#9)\n'
    '10. [**Multi-kapal dan Objective ETA**](#10)\n'
    '11. [**Batas Atas dan Optimum Eksak**](#11)\n'
    '12. [**Pasca-Analisis**](#12)\n'
    '13. [**Daftar Pustaka**](#13)'
))

cells.append(section('Pendahuluan', '1'))
cells.append(md(
    '## Persoalan\n\n'
    'Kapal pengangkut kendaraan menerima muatan dengan ukuran, berat, tarif pengiriman, dan ETA yang berbeda. '
    'Seluruh kendaraan tidak selalu dapat dimuat karena luas geladak dan kapasitas berat terbatas. '
    '**CARGO** menentukan kendaraan yang diangkut beserta posisi dan orientasinya untuk memaksimalkan pendapatan pengiriman.\n\n'
    '- **Tugas**: pemilihan muatan dan penataan persegi panjang pada grid dua dimensi.\n'
    '- **Objective wajib**: total *shipping fee* kendaraan yang dimuat.\n'
    '- **Kendala**: tidak overlap, seluruh kendaraan di dalam batas geladak, dan berat tidak melebihi kapasitas.\n'
    '- **Platform**: Python pada CPU; tidak membutuhkan GPU, pelatihan model, atau layanan eksternal.'
))
cells.append(md(
    '## Dataset\n\n'
    'Data persoalan disimpan sebagai JSON dengan dua entitas, yaitu `ships` dan `vehicles`. '
    'Setiap kapal mempunyai dimensi serta kapasitas, sedangkan kendaraan mempunyai dimensi, fee, berat, dan ETA. '
    '`main.json` digunakan bersama oleh eksperimen wajib, `multi.json` untuk armada, dan `small.json` untuk optimum eksak. '
    'Seed dan parameter generator tersimpan pada metadata input.'
))
cells.append(md(
    '## Pendekatan: CARGO\n\n'
    '**Constraint-Aware Revenue and Geometric Optimization** merupakan kerangka optimasi berbasis *local search*. '
    'Hill-Climbing, Simulated Annealing, dan Genetic Algorithm menggunakan representasi posisi serta evaluator yang sama, '
    'sehingga perbedaan hasil dapat ditelusuri pada mekanisme pencarian dan budget masing-masing.\n\n'
    '```text\n'
    'Input JSON: kapal dan kendaraan\n'
    '    |\n'
    '    +-- State: kapal, koordinat, dan orientasi per kendaraan\n'
    '    +-- Evaluator: shipping fee - penalty pelanggaran\n'
    '         |\n'
    '    Hill-Climbing / Simulated Annealing / Genetic Algorithm\n'
    '         |\n'
    '    Incumbent feasible -> hasil JSON -> visualisasi dan analisis\n'
    '```\n\n'
    'State awal diacak dan boleh infeasible. State akhir diambil dari incumbent feasible terbaik; '
    'kapal kosong menjadi baseline eksplisit apabila pencarian belum menemukan state feasible. '
    'Notebook ini membaca hasil resmi yang sudah disimpan, bukan menjalankan ulang seluruh search.'
))
cells.append(md(
    '## Objective dan Metrik\n\n'
    'Objective penalized digunakan untuk menjelajahi penempatan sementara yang melanggar kendala. '
    'Pada solusi feasible, nilainya sama dengan pendapatan pengiriman. Kualitas akhir dibaca bersama durasi, '
    'jumlah evaluasi, utilisasi muatan, dan variasi antar-seed.\n\n'
    '$$f(s) = \\sum_{i\\;\\mathrm{dimuat}} fee_i - P\\,(overlap + out\\_of\\_bounds + weight\\_units)$$\n\n'
    '$$gap_{UB} = \\frac{UB - f(s)}{UB}$$\n\n'
    '`UB` adalah relaksasi luas dan berat, bukan optimum geometris yang sudah dibuktikan. '
    'Nilai eksak hanya dihitung untuk instance kecil.'
))
cells.append(md(
    '## Referensi Utama\n\n'
    '- [Laporan tugas besar](../docs/TugasBesar1_Sepakat.pdf) - state, objective, neighborhood, algoritma, heuristik, dan analisis hasil.\n'
    '- [Ringkasan hasil resmi](../output/experiments/summary.md) - tabel seluruh run.\n'
    '- Materi kuliah IF3070_Materi03-BeyondClassicalSearch: Hill-Climbing (slide 20-30), Simulated Annealing (slide 31-40), dan Genetic Algorithm (slide 41-50).'
))

cells.append(section('Inisialisasi', '2'))
cells.append(md(
    'Bagian ini menyiapkan lingkungan analisis, memusatkan konfigurasi, dan memuat artefak eksperimen. '
    'Eksekusi hanya menggunakan data lokal; hasil pencarian resmi tidak ditulis ulang.'
))
cells.append(md(
    '## Environment\n\n'
    '> **Catatan reproduksi:** aktifkan environment proyek, lalu jalankan *Run All*. '
    'Apabila artefak resmi belum tersedia, jalankan `python src/experiments.py` dari root repository terlebih dahulu. '
    'Notebook dapat dibuka dari root atau direktori `notebooks/` dan tidak memerlukan direktori template.'
))
cells.append(md(
    '## Instalasi\n\n'
    'Seluruh pustaka dipasang melalui `python -m pip install -r requirements.txt` dari root repository. '
    'Matplotlib menangani gambar, IPython menampilkan tabel dan keluaran visual, sedangkan nbclient digunakan oleh builder untuk eksekusi otomatis. '
    'Instalasi tidak dijalankan otomatis saat notebook dieksekusi agar lingkungan dan versi paket tidak berubah di tengah analisis.'
))
cells.append(md('## Pustaka'))
cells.append(md(
    'Seluruh impor dikelompokkan dalam satu sel. Modul proyek menyediakan pemuatan input, evaluasi state, '
    'rencana eksperimen, dan visualisasi; kode analisis di bawah mempertahankan nilai hasil run yang sudah tersimpan.'
))
cells.append(code(
    'import math\n'
    'import platform\n'
    'import random\n'
    'import sys\n'
    'from collections import Counter\n'
    'from html import escape\n'
    'from pathlib import Path\n'
    'from statistics import mean, stdev\n\n'
    'import matplotlib.pyplot as plt\n'
    'from IPython.display import HTML, Image, Markdown, display\n\n'
    "ROOT = next((p for p in (Path.cwd(), *Path.cwd().parents) if (p / 'src' / 'experiments.py').is_file()), None)\n"
    'if ROOT is None:\n'
    "    raise FileNotFoundError('Buka notebook dari root repository atau direktori notebooks/.')\n"
    "sys.path.insert(0, str(ROOT / 'src'))\n\n"
    'from config import DATA_DIR, EXPERIMENTS_DIR, OUTPUT_DIR\n'
    'from core.bounds import brute_force, upper_bound\n'
    'from core.eta_objective import eta_problem, shipping_fee_total, urgency_weight\n'
    'from core.problem import load_problem\n'
    'from core.state import State\n'
    'from experiments import comparison_groups, load_results, machine_info, planned_runs\n'
    'from visualization.plots import plot_objective, plot_run, plot_summary\n'
    'from visualization.state_view import draw_state\n\n'
    "print('Python :', sys.version.split()[0])\n"
    "print('OS     :', platform.system(), platform.release())\n"
    "print('CWD    :', Path.cwd())\n"
    "print('Device : CPU')"
))
cells.append(md('## Seed'))
cells.append(md(
    'Seed analisis ditetapkan untuk menjaga reproduksibilitas operasi random tambahan. '
    'Seed pencarian tidak diubah: setiap run tetap memakai seed yang tersimpan dalam JSON masing-masing.'
))
cells.append(code(
    'def seed_everything(seed: int = 42):\n'
    '    random.seed(seed)\n\n'
    'seed_everything(42)'
))
cells.append(md('## Settings'))
cells.append(md(
    'Kelas `Settings` memusatkan jalur data, jumlah run yang diharapkan, label algoritma, dan pengaturan gambar. '
    'Gambar analisis diekspor ke `output/analysis/`; JSON dan gambar eksperimen resmi tetap berada di direktori aslinya.'
))
cells.append(code(
    'class Settings:\n'
    '    SEED              = 42\n'
    "    NAME              = 'CARGO'\n\n"
    '    # Paths\n'
    '    DATA_DIR          = DATA_DIR\n'
    '    EXPERIMENT_DIR    = EXPERIMENTS_DIR\n'
    "    FIG_DIR           = OUTPUT_DIR / 'analysis'\n\n"
    '    # Experiment protocol\n'
    '    EXPECTED_RUNS     = 39\n'
    '    EXPECTED_REQUIRED = 24\n'
    '    EXACT_MAX_NODES   = 5_000_000\n\n'
    '    # Visualisation\n'
    '    FIG_DPI           = 120\n'
    "    COLORS            = ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9']\n"
    '    ALGO_NAMES        = {\n'
    "        'steepest': 'Steepest Ascent', 'stochastic': 'Stochastic HC',\n"
    "        'sideways': 'Sideways Move', 'random_restart': 'Random Restart',\n"
    "        'sa': 'Simulated Annealing', 'ga': 'Genetic Algorithm',\n"
    '    }\n'
    '    GROUP_NAMES       = {\n'
    "        'hc': 'Steepest Ascent', 'sa': 'Simulated Annealing',\n"
    "        'ga_iter': 'GA: Variasi Generasi', 'ga_pop': 'GA: Variasi Populasi',\n"
    "        'hc_variants': 'Varian Hill-Climbing', 'eta': 'Objective ETA', 'multi': 'Multi-kapal',\n"
    '    }\n\n'
    'CFG = Settings()\n'
    'CFG.FIG_DIR.mkdir(parents=True, exist_ok=True)\n'
    "plt.rcParams.update({'font.size': 10, 'axes.titlesize': 11, 'axes.labelsize': 10,\n"
    "                     'legend.fontsize': 8, 'axes.grid': True, 'grid.alpha': 0.2,\n"
    "                     'axes.prop_cycle': plt.cycler(color=CFG.COLORS), 'figure.dpi': 100})\n\n"
    "print(f'DATA_DIR       : {CFG.DATA_DIR}')\n"
    "print(f'EXPERIMENT_DIR : {CFG.EXPERIMENT_DIR}')\n"
    "print(f'FIG_DIR        : {CFG.FIG_DIR}')\n"
    "print('Mesin analisis :', machine_info())"
))
cells.append(md('## Muat Dataset dan Artefak'))
cells.append(md(
    'Rencana eksperimen menentukan file yang dibaca agar run manual atau quick tidak tercampur ke hasil resmi. '
    'Setiap sweep GA harus memuat sembilan eksekusi, termasuk kontrol yang disimpan terpisah. '
    'Pemeriksaan kelengkapan dijalankan sebelum membuat tabel dan gambar.'
))
cells.append(code(
    'plan = planned_runs()\n'
    'assert len(plan) == CFG.EXPECTED_RUNS\n'
    'assert sum(run.required for run in plan) == CFG.EXPECTED_REQUIRED\n'
    'assert all(len(run.groups) == 1 for run in plan)\n'
    'assert len({run.path(CFG.EXPERIMENT_DIR) for run in plan}) == len(plan)\n'
    "for group in ('ga_iter', 'ga_pop'):\n"
    '    assert sum(run.groups[0] == group for run in plan) == 9\n\n'
    'missing = []\n'
    'for run in plan:\n'
    '    path = run.path(CFG.EXPERIMENT_DIR)\n'
    "    artifacts = [path, *(path.with_name(path.stem + suffix) for suffix in ('_initial.png', '_final.png', '_plot.png'))]\n"
    '    missing.extend(str(p.relative_to(ROOT)) for p in artifacts if not p.is_file())\n'
    'if missing:\n'
    "    raise FileNotFoundError('Jalankan python src/experiments.py terlebih dahulu.\\n' + '\\n'.join(missing))\n\n"
    'pairs = load_results(plan, CFG.EXPERIMENT_DIR)\n'
    'assert len(pairs) == len(plan)\n'
    'problems = {path: load_problem(path) for path in dict.fromkeys(run.instance for run in plan)}\n'
    "main_problem = load_problem(CFG.DATA_DIR / 'main.json')\n\n"
    "print(f'Input utama : {len(main_problem.vehicles)} kendaraan, {len(main_problem.ships)} kapal')\n"
    "print(f'Run resmi   : {len(pairs)}')\n"
    "print(f'Run wajib   : {sum(run.required for run in plan)}')"
))
cells.append(md('## Utilitas Penyajian'))
cells.append(md(
    'Tabel ditampilkan sebagai HTML dengan header dan baris yang tetap terbaca ketika kolomnya banyak. '
    'Setiap figure disimpan sebagai PNG serta ditanam langsung ke output notebook, sehingga hasil visual tetap terlihat '
    'setelah kernel ditutup atau notebook dibuka melalui penampil statis.'
))
cells.append(code(
    'def of(group, algorithm=None):\n'
    '    return [(run, result) for run, result in pairs\n'
    '            if run.groups[0] == group and (algorithm is None or run.algo == algorithm)]\n\n'
    'def table(headers, rows):\n'
    "    head = ''.join(f'<th>{escape(str(value))}</th>' for value in headers)\n"
    "    body = ''.join('<tr>' + ''.join(f'<td>{escape(str(value))}</td>' for value in row) + '</tr>' for row in rows)\n"
    "    display(HTML('<div style=\"overflow-x:auto; margin:12px 0\">'\n"
    "                 '<table class=\"dataframe\" style=\"border-collapse:collapse; font-size:13px; white-space:nowrap\">'\n"
    "                 f'<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'))\n\n"
    'def insights(text):\n'
    "    display(Markdown('> ### Insights\\n> ' + text.replace('\\n\\n', '\\n>\\n> ')))\n\n"
    'def show(fig, filename):\n'
    '    path = CFG.FIG_DIR / filename\n'
    "    fig.savefig(path, dpi=CFG.FIG_DPI, bbox_inches='tight')\n"
    "    caption = ' | '.join(axis.get_title() for axis in fig.axes if axis.get_title())\n"
    '    display(Image(filename=str(path), alt=caption or filename))\n'
    '    plt.close(fig)\n'
    "    print('Gambar:', path.relative_to(ROOT))"
))

cells.append(section('Analisis Data Eksploratif', '3'))
cells.append(md(
    'Analisis data dilakukan pada input persoalan sebelum membandingkan algoritma. '
    'Distribusi dimensi, berat, dan fee memperlihatkan tingkat persaingan antarkendaraan terhadap kapasitas yang tersedia.'
))
cells.append(md('## Karakteristik Instance'))
cells.append(md(
    'Luas dan berat seluruh kandidat dibandingkan dengan kapasitas setiap instance. '
    'Rasio di atas satu menunjukkan bahwa seluruh kendaraan tidak dapat dimuat sekaligus, '
    'bahkan sebelum susunan geometris diperhitungkan.'
))
cells.append(code(
    'instance_rows = []\n'
    'for problem in [main_problem, *(p for p in problems.values() if p.name != main_problem.name)]:\n'
    '    deck_area = sum(ship.area for ship in problem.ships)\n'
    '    capacity = sum(ship.max_capacity for ship in problem.ships)\n'
    '    total_area = sum(vehicle.area for vehicle in problem.vehicles)\n'
    '    total_weight = sum(vehicle.weight for vehicle in problem.vehicles)\n'
    '    instance_rows.append([problem.name, len(problem.ships), len(problem.vehicles),\n'
    "                          f'{total_area}/{deck_area}', f'{total_weight:g}/{capacity:g}',\n"
    "                          f'{total_area / deck_area:.2f}x', f'{total_weight / capacity:.2f}x'])\n"
    "table(['Instance', 'Kapal', 'Kendaraan', 'Luas kandidat/deck', 'Berat kandidat/kapasitas', 'Rasio luas', 'Rasio berat'], instance_rows)\n\n"
    'main_area = sum(v.area for v in main_problem.vehicles)\n'
    'main_capacity = sum(ship.max_capacity for ship in main_problem.ships)\n'
    'main_weight = sum(v.weight for v in main_problem.vehicles)\n'
    "insights(f'Pada instance utama, luas kandidat {main_area} sel dan berat {main_weight:g} unit '\n"
    "         f'bersaing untuk {sum(s.area for s in main_problem.ships)} sel dan kapasitas {main_capacity:g} unit. '\n"
    "         'Pemilihan kendaraan diperlukan; penataan saja tidak cukup untuk membawa seluruh kandidat.')"
))
cells.append(md('## Distribusi Dimensi dan Nilai Muatan'))
cells.append(md(
    'Distribusi ukuran menunjukkan bentuk kendaraan yang paling sering muncul. '
    'Hubungan berat dan fee membantu membaca potensi trade-off antara kendaraan yang mahal dan kendaraan yang lebih ringan; '
    'titik pada scatter tetap mewakili kendaraan individual, bukan hasil prediksi.'
))
cells.append(code(
    "dimension_counts = Counter(f'{v.width}x{v.length}' for v in main_problem.vehicles)\n"
    'labels = sorted(dimension_counts, key=lambda label: tuple(int(value) for value in label.split(\'x\')))\n'
    'counts = [dimension_counts[label] for label in labels]\n\n'
    'fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.5))\n'
    'bars = ax1.bar(labels, counts, color=CFG.COLORS[0], edgecolor=\'white\')\n'
    'ax1.bar_label(bars, padding=3)\n'
    "ax1.set(xlabel='Dimensi kendaraan (grid)', ylabel='Jumlah kendaraan', title='Distribusi Dimensi Kendaraan')\n"
    'scatter = ax2.scatter([v.weight for v in main_problem.vehicles],\n'
    '                      [v.shipping_fee for v in main_problem.vehicles],\n'
    "                      c=[v.eta for v in main_problem.vehicles], cmap='viridis', edgecolors='white', s=65)\n"
    "ax2.set(xlabel='Berat (unit)', ylabel='Shipping fee (juta rupiah)', title='Berat, Fee, dan ETA')\n"
    "fig.colorbar(scatter, ax=ax2, label='ETA (hari)')\n"
    "fig.suptitle('Karakteristik Kandidat Muatan', fontsize=13, fontweight='bold')\n"
    'plt.tight_layout()\n'
    "show(fig, '01_vehicle_characteristics.png')\n\n"
    "print(f'Fee   -- min: {min(v.shipping_fee for v in main_problem.vehicles):g} | mean: {mean(v.shipping_fee for v in main_problem.vehicles):.2f} | max: {max(v.shipping_fee for v in main_problem.vehicles):g}')\n"
    "print(f'Berat -- min: {min(v.weight for v in main_problem.vehicles):g} | mean: {mean(v.weight for v in main_problem.vehicles):.2f} | max: {max(v.weight for v in main_problem.vehicles):g}')"
))
cells.append(md(
    '> ### Insights\n'
    '> Kendaraan dengan fee tinggi juga menggunakan luas dan kapasitas berat. Rasio fee per sel atau per unit berat '
    'dapat membantu interpretasi, tetapi belum menjamin pilihan terbaik karena kendaraan tetap harus dapat disusun tanpa overlap.'
))
cells.append(md('## Verifikasi Hasil terhadap Input'))
cells.append(md(
    'Seluruh state tersimpan direkonstruksi dari input yang tepat. Evaluator menghitung ulang objective, feasibility, fee, '
    'dan upper bound; gambar pasangan run juga diperiksa agar analisis tidak bergantung pada ringkasan yang tidak konsisten.'
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
    "    for stage in ('initial', 'final'):\n"
    "        state = State.from_dict(problem, result[stage + '_state'])\n"
    '        evaluation = state.evaluate()\n'
    "        assert math.isclose(evaluation.objective, result[stage + '_objective'], abs_tol=1e-7)\n"
    "        if stage == 'final':\n"
    "            assert evaluation.is_feasible and result['is_feasible']\n"
    "            assert math.isclose(evaluation.total_fee, result['total_fee'], abs_tol=1e-7)\n"
    "            if run.objective == 'eta':\n"
    "                assert math.isclose(shipping_fee_total(original, state.positions), result['extra']['shipping_fee_total'], abs_tol=1e-7)\n"
    '    bound = upper_bound(problem)\n'
    "    assert math.isclose(bound, result['upper_bound'], abs_tol=1e-7)\n"
    "    assert result['final_objective'] <= bound + 1e-7\n"
    '    if bound:\n'
    "        assert math.isclose((bound - result['final_objective']) / bound, result['gap_ub'], abs_tol=1e-7)\n"
    '    path = run.path(CFG.EXPERIMENT_DIR)\n'
    "    for suffix in ('_initial.png', '_final.png', '_plot.png'):\n"
    '        assert plt.imread(path.with_name(path.stem + suffix)).size > 0\n'
    "    audit.append([run.groups[0], run.algo, run.seed, result['extra']['empty_baseline_used']])\n\n"
    "print(f'State akhir tervalidasi : {len(audit)}')\n"
    "print(f'Baseline kosong        : {sum(row[3] for row in audit)}')\n"
    "insights(f'Seluruh {len(audit)} state akhir lolos evaluasi ulang. '\n"
    "         'Validitas fisik diperiksa dari penempatan, bukan diasumsikan dari angka objective akhir.')"
))

cells.append(section('Protokol dan Hasil Eksperimen', '4'))
cells.append(md(
    'Setiap konfigurasi menggunakan tiga seed. Dua sweep GA dilaksanakan terpisah: populasi menjadi kontrol saat generasi '
    'divariasikan, kemudian generasi menjadi kontrol saat populasi divariasikan. Parameter lain dipertahankan.'
))
cells.append(md('## Cakupan Eksperimen'))
cells.append(md(
    'Daftar berikut memisahkan eksperimen wajib dan bonus. Pengulangan kontrol GA memenuhi pelaksanaan kedua sweep, '
    'tetapi pasangan parameter dan seed yang identik tidak dihitung sebagai sampel independen tambahan pada perbandingan kualitas.'
))
cells.append(code(
    'group_counts = Counter(run.groups[0] for run in plan)\n'
    "table(['Grup', 'Eksperimen', 'Run', 'Kategori'],\n"
    '      [[group, CFG.GROUP_NAMES[group], count,\n'
    "        'Wajib' if any(run.required for run in plan if run.groups[0] == group) else 'Bonus']\n"
    '       for group, count in group_counts.items()])\n\n'
    "print(f'Total : {len(plan)} run, termasuk {sum(run.required for run in plan)} run wajib')"
))
cells.append(md('## Hasil Setiap Run'))
cells.append(md(
    'Tabel menampilkan hasil per seed, bukan hanya run terbaik. Fee asli dipisahkan dari objective ETA, '
    'sedangkan durasi berasal dari proses pencarian yang dicatat dalam JSON. '
    'Mengulang notebook hanya menghitung tabel dan menggambar hasil, tidak menghasilkan waktu search baru.'
))
cells.append(code(
    'for group in group_counts:\n'
    "    display(Markdown('### ' + CFG.GROUP_NAMES[group]))\n"
    '    rows = []\n'
    '    for run, result in of(group):\n'
    "        params = result['params']\n"
    "        setup = f\"pop={params['population']}, gen={params['iterations']}\" if run.algo == 'ga' else CFG.ALGO_NAMES[run.algo]\n"
    "        revenue = result['extra'].get('shipping_fee_total', result['total_fee'])\n"
    "        rows.append([run.seed, setup, f\"{result['initial_objective']:.2f}\",\n"
    "                     f\"{result['final_objective']:.2f}\", f'{revenue:.2f}', result['is_feasible'],\n"
    "                     result['iterations'], result['evaluations'], f\"{result['duration_s']:.3f}\"])\n"
    "    table(['Seed', 'Konfigurasi', 'Obj awal', 'Obj akhir', 'Fee asli', 'Feasible', 'Iterasi', 'Evaluasi', 'Durasi (s)'], rows)"
))
cells.append(md(
    '> ### Insights\n'
    '> Nilai akhir merupakan incumbent feasible, sedangkan kurva berikut tetap memperlihatkan objective berjalan atau '
    'maksimum populasi. Perbedaan tersebut penting ketika search masih berada pada susunan berpenalti.'
))

cells.append(section('Hill-Climbing', '5'))
cells.append(md(
    'Hill-Climbing memperbaiki konfigurasi melalui neighborhood move, swap, dan rotate. '
    'Empat varian dibedakan oleh pemilihan neighbor, penerimaan nilai setara, atau pengulangan initial state.'
))
cells.append(md('## Varian dan Penghentian'))
cells.append(md(
    'Steepest Ascent memeriksa seluruh neighborhood; Stochastic memeriksa proposal random; Sideways menerima perpindahan '
    'bernilai setara sampai batas total; Random Restart menjalankan Steepest kembali dari initial acak baru. '
    'Jumlah evaluasi karena itu tidak dapat disamakan dengan jumlah iterasi.'
))
cells.append(code(
    "hc_pairs = of('hc') + of('hc_variants')\n"
    'hc_rows = []\n'
    'for run, result in hc_pairs:\n'
    "    params, extra = result['params'], result['extra']\n"
    "    limit = (f\"sideways={params['max_sideways']}\" if run.algo == 'sideways' else\n"
    "             f\"restart={params['max_restart']}\" if run.algo == 'random_restart' else\n"
    "             f\"no_improve={params['max_no_improve']}\" if run.algo == 'stochastic' else\n"
    "             f\"iter_max={params['max_iterations']}\")\n"
    "    detail = ', '.join(str(value) for value in extra['iters_per_restart']) if run.algo == 'random_restart' else str(extra.get('sideways_moves', '-'))\n"
    "    stop = ', '.join(sorted(set(extra['stop_reasons']))) if run.algo == 'random_restart' else extra['stop_reason']\n"
    '    hc_rows.append([CFG.ALGO_NAMES[run.algo], run.seed, limit,\n'
    "                    extra.get('restarts', '-'), detail, stop])\n"
    "table(['Varian', 'Seed', 'Batas', 'Restart', 'Sideways / iterasi tiap percobaan', 'Stop reason'], hc_rows)"
))
cells.append(md('## Kurva Konvergensi'))
cells.append(md(
    'Satu baris gambar digunakan untuk satu varian dan tiga seed. Nilai negatif tetap terlihat untuk memperlihatkan '
    'pemulihan dari initial infeasible, sementara garis incumbent menunjukkan muatan valid terbaik yang sudah ditemukan.'
))
cells.append(code(
    "hc_algorithms = ('steepest', 'stochastic', 'sideways', 'random_restart')\n"
    'for algo in hc_algorithms:\n'
    '    selected = sorted([(run, result) for run, result in hc_pairs if run.algo == algo], key=lambda pair: pair[0].seed)\n'
    '    fig, axes = plt.subplots(1, 3, figsize=(14, 4))\n'
    '    for ax, (run, result) in zip(axes, selected):\n'
    '        plot_objective(ax, result)\n'
    "        ax.set_title(f\"Seed {run.seed}: {result['iterations']} iterasi\", fontsize=10)\n"
    "    fig.suptitle(CFG.ALGO_NAMES[algo], fontsize=13, fontweight='bold')\n"
    '    plt.tight_layout()\n'
    "    show(fig, f'03_hc_{algo}.png')\n\n"
    "hc_means = {algo: mean(result['final_objective'] for run, result in hc_pairs if run.algo == algo) for algo in hc_algorithms}\n"
    "insights('Mean objective akhir: ' + '; '.join(f'{CFG.ALGO_NAMES[algo]} = {value:.2f}' for algo, value in hc_means.items()) + '. '\n"
    "         'Hasil antarvarian dibaca bersama biaya evaluasi dan parameter penghentiannya.')"
))

cells.append(section('Simulated Annealing', '6'))
cells.append(md(
    'Simulated Annealing dapat menerima perpindahan yang memperburuk objective dengan peluang `exp(delta/T)`. '
    'Suhu diturunkan secara geometris; T0 berasal dari sampel neighbor awal. '
    'Mekanisme ini memungkinkan pencarian meninggalkan konfigurasi yang tidak dapat dilewati HC biasa.'
))
cells.append(md('## Objective dan Peluang Penerimaan'))
cells.append(md(
    'Setiap seed ditampilkan dengan dua panel: objective terhadap iterasi dan peluang menerima langkah dengan delta negatif. '
    'Peluang bukan persentase keberhasilan; incumbent feasible tetap menjadi dasar solusi akhir.'
))
cells.append(code(
    "sa_results = [result for run, result in of('sa')]\n"
    "for run, result in of('sa'):\n"
    '    fig = plot_run(result)\n'
    '    fig.set_size_inches(14, 4.5)\n'
    "    show(fig, f'04_sa_seed{run.seed}.png')"
))
cells.append(md('## Stuck dan Stagnasi'))
cells.append(md(
    'Local optimum dikonfirmasi melalui pemeriksaan neighborhood pada checkpoint. '
    'Episode dihitung sekali untuk rangkaian checkpoint local-optimum yang berurutan. '
    'Stagnasi best-so-far dicatat terpisah, karena tidak adanya rekor baru belum membuktikan bahwa semua neighbor lebih buruk.'
))
cells.append(code(
    "table(['Seed', 'T0', 'Alpha', 'Interval cek', 'Episode stuck', 'Stagnasi', 'Evaluasi konfirmasi'],\n"
    "      [[r['seed'], f\"{r['extra']['t0']:.2f}\", f\"{r['extra']['alpha']:.6f}\",\n"
    "        r['params']['stuck_window'], r['extra']['stuck_count'], r['extra']['stagnation_count'],\n"
    "        r['extra']['confirmation_evaluations']] for r in sa_results])\n\n"
    "insights(f\"Mean objective SA = {mean(r['final_objective'] for r in sa_results):.2f}; \"\n"
    "         f\"mean episode stuck teramati = {mean(r['extra']['stuck_count'] for r in sa_results):.2f}. \"\n"
    "         'Kunjungan di antara checkpoint dapat tidak terdeteksi. Biaya konfirmasi sudah termasuk jumlah evaluasi dan durasi SA.')"
))

cells.append(section('Genetic Algorithm', '7'))
cells.append(md(
    'Genetic Algorithm mempertahankan populasi konfigurasi kendaraan. Seleksi roulette memakai fitness positif hasil '
    'windowing; crossover satu titik, mutasi neighbor, dan elitism membentuk generasi berikutnya. '
    'Karena koordinat antarkendaraan saling bergantung, offspring crossover dapat kembali overlap.'
))
cells.append(md('## Kontrol Populasi, Variasi Generasi'))
cells.append(md(
    'Populasi ditahan pada nilai kontrol dan generasi divariasikan. '
    'Tiap gambar memuat tiga seed untuk satu konfigurasi agar maksimum serta rata-rata populasi tetap terbaca.'
))
cells.append(code(
    "ga_iter_pairs = of('ga_iter')\n"
    "for generations in sorted({result['params']['iterations'] for run, result in ga_iter_pairs}):\n"
    "    selected = [(run, result) for run, result in ga_iter_pairs if result['params']['iterations'] == generations]\n"
    '    fig, axes = plt.subplots(1, 3, figsize=(14, 4))\n'
    '    for ax, (run, result) in zip(axes, selected):\n'
    '        plot_objective(ax, result)\n'
    "        ax.set_title(f\"Seed {run.seed}: objective {result['final_objective']:g}\", fontsize=10)\n"
    "    population = selected[0][1]['params']['population']\n"
    "    fig.suptitle(f'GA: Populasi {population}, Generasi {generations}', fontsize=13, fontweight='bold')\n"
    '    plt.tight_layout()\n'
    "    show(fig, f'05_ga_generations_{generations}.png')"
))
cells.append(md(
    '> ### Insights\n'
    '> Generasi tambahan memperpanjang kesempatan eksplorasi pada ukuran populasi yang sama. '
    'Jarak antara maksimum dan rata-rata populasi memperlihatkan bahwa kualitas individu terbaik tidak mewakili seluruh offspring.'
))
cells.append(md('## Kontrol Generasi, Variasi Populasi'))
cells.append(md(
    'Generasi ditahan pada nilai kontrol dan populasi divariasikan. '
    'Kontrol dijalankan lagi untuk sweep ini, bukan memakai satu pelaksanaan yang sama dengan sweep sebelumnya.'
))
cells.append(code(
    "ga_pop_pairs = of('ga_pop')\n"
    "for population in sorted({result['params']['population'] for run, result in ga_pop_pairs}):\n"
    "    selected = [(run, result) for run, result in ga_pop_pairs if result['params']['population'] == population]\n"
    '    fig, axes = plt.subplots(1, 3, figsize=(14, 4))\n'
    '    for ax, (run, result) in zip(axes, selected):\n'
    '        plot_objective(ax, result)\n'
    "        ax.set_title(f\"Seed {run.seed}: objective {result['final_objective']:g}\", fontsize=10)\n"
    "    generations = selected[0][1]['params']['iterations']\n"
    "    fig.suptitle(f'GA: Generasi {generations}, Populasi {population}', fontsize=13, fontweight='bold')\n"
    '    plt.tight_layout()\n'
    "    show(fig, f'06_ga_population_{population}.png')"
))
cells.append(md('## Pengaruh Budget Pencarian'))
cells.append(md(
    'Mean dan simpangan baku tiap konfigurasi dibandingkan bersama durasi serta evaluasi. '
    'Kenaikan populasi maupun generasi menambah budget komputasi, sehingga perubahan kualitas tidak dibaca terpisah dari biayanya.'
))
cells.append(code(
    'ga_budget_rows = []\n'
    "for group, key in (('ga_iter', 'iterations'), ('ga_pop', 'population')):\n"
    '    members = of(group)\n'
    "    for value in sorted({result['params'][key] for run, result in members}):\n"
    "        selected = [result for run, result in members if result['params'][key] == value]\n"
    "        ga_budget_rows.append([group, value, mean(r['final_objective'] for r in selected),\n"
    "                               stdev(r['final_objective'] for r in selected),\n"
    "                               mean(r['duration_s'] for r in selected), mean(r['evaluations'] for r in selected)])\n"
    "table(['Sweep', 'Parameter', 'Obj mean', 'Obj std', 'Durasi mean (s)', 'Evaluasi mean'],\n"
    "      [[*row[:2], *(f'{value:.3f}' for value in row[2:])] for row in ga_budget_rows])\n\n"
    "for group in ('ga_iter', 'ga_pop'):\n"
    '    rows = [row for row in ga_budget_rows if row[0] == group]\n'
    '    low, high = rows[0], rows[-1]\n'
    "    insights(f'{CFG.GROUP_NAMES[group]}: parameter {low[1]} ke {high[1]} memberi perubahan mean objective '\n"
    "             f'{high[2] - low[2]:+.2f}, durasi {high[4] - low[4]:+.3f} s, dan evaluasi {high[5] - low[5]:+.0f}. '\n"
    "             'Hasil tersebut berlaku pada konfigurasi dan seed yang dibandingkan.')"
))

cells.append(section('Perbandingan Algoritma', '8'))
cells.append(md(
    'Perbandingan memakai objective fee pada instance utama. GA diwakili konfigurasi dengan mean tertinggi dari sweep. '
    'Pengulangan kontrol dengan seed sama dihitung sekali agar ringkasan tidak memperlakukan keluaran deterministik sebagai sampel baru.'
))
cells.append(md('## Kualitas, Durasi, dan Konsistensi'))
cells.append(md(
    'Tabel merangkum seluruh seed, sementara box plot menampilkan sebaran objective akhir dan titik setiap run. '
    'Durasi merupakan waktu pencarian tersimpan, termasuk monitoring neighborhood pada SA.'
))
cells.append(code(
    'compare = comparison_groups(pairs)\n'
    'comparison = []\n'
    'for label, results in compare.items():\n'
    "    finals = [result['final_objective'] for result in results]\n"
    '    comparison.append([label, len(results), max(finals), mean(finals), stdev(finals),\n'
    "                       mean(r['duration_s'] for r in results), mean(r['evaluations'] for r in results),\n"
    "                       100 * mean(r['gap_ub'] for r in results)])\n"
    "table(['Algoritma', 'n', 'Best', 'Mean', 'Std', 'Durasi (s)', 'Evaluasi', 'Gap UB (%)'],\n"
    "      [[row[0], row[1], *(f'{value:.3f}' for value in row[2:])] for row in comparison])\n\n"
    'labels = {id(result): label for label, results in compare.items() for result in results}\n'
    'fig = plot_summary([result for results in compare.values() for result in results], group=lambda result: labels[id(result)])\n'
    'fig.set_size_inches(14, 5)\n'
    "show(fig, '07_algorithm_comparison.png')\n\n"
    'best_quality = max(comparison, key=lambda row: row[3])\n'
    'fastest = min(comparison, key=lambda row: row[5])\n'
    'consistent = min(comparison, key=lambda row: row[4])\n'
    "insights(f'Mean kualitas tertinggi: {best_quality[0]} ({best_quality[3]:.2f}); '\n"
    "         f'durasi mean terendah: {fastest[0]} ({fastest[5]:.3f} s); '\n"
    "         f'simpangan baku terendah: {consistent[0]} ({consistent[4]:.2f}). '\n"
    "         'Ketiga ukuran menjawab pertanyaan berbeda; variansi rendah pada objective rendah tidak menunjukkan solusi terbaik.')"
))
cells.append(md('## Konvergensi terhadap Evaluasi Aktual'))
cells.append(md(
    'Sumbu horizontal menggunakan hitungan kumulatif `history.evaluations`, bukan interpolasi dari total evaluasi. '
    'Kurva memilih satu run terbaik tiap algoritma dan menampilkan incumbent feasible dengan garis bertangga.'
))
cells.append(code(
    'fig, ax = plt.subplots(figsize=(14, 4.5))\n'
    'for label, results in compare.items():\n'
    "    result = max(results, key=lambda item: item['final_objective'])\n"
    "    x = result['history']['evaluations']\n"
    "    y = result['history']['best_feasible']\n"
    "    assert len(x) == len(y) == result['iterations'] + 1\n"
    "    assert x[-1] == result['evaluations']\n"
    '    assert all(right >= left for left, right in zip(x, x[1:]))\n'
    "    ax.step(x, y, where='post', label=f\"{label}, seed {result['seed']}\")\n"
    "ax.set(xlabel='Evaluasi kumulatif', ylabel='Incumbent feasible', title='Konvergensi Run Terbaik per Algoritma')\n"
    'ax.legend(fontsize=8)\n'
    'plt.tight_layout()\n'
    "show(fig, '08_actual_evaluations.png')"
))
cells.append(md(
    '> ### Insights\n'
    '> Satu delta probe tidak selalu berbiaya sama dengan penilaian individu GA. '
    'Kurva evaluasi menjelaskan pekerjaan algoritma, sedangkan durasi tetap diperlukan untuk membandingkan biaya pada mesin yang digunakan.'
))

cells.append(section('Visualisasi Penataan Kendaraan', '9'))
cells.append(md(
    'State awal dan akhir dari run terbaik setiap algoritma ditampilkan berpasangan. '
    'Gambar diambil dari artefak run yang sama, sehingga visualisasi tidak menggunakan pencarian baru dengan hasil berbeda.'
))
cells.append(md('## Initial State dan Final State'))
cells.append(md(
    'Warna dan id kendaraan dipertahankan antargambar. Arsir merah serta garis putus-putus menunjukkan pelanggaran pada initial state, '
    'sedangkan panel luar kapal memperlihatkan kandidat yang tidak diangkut. Judul setiap pasangan mencantumkan seed dan objective akhir.'
))
cells.append(code(
    'for label, results in compare.items():\n'
    "    best = max(results, key=lambda result: result['final_objective'])\n"
    '    run = next(run for run, result in pairs if result is best)\n'
    '    path = run.path(CFG.EXPERIMENT_DIR)\n'
    '    fig, axes = plt.subplots(1, 2, figsize=(14, 8))\n'
    "    for ax, stage, title in zip(axes, ('initial', 'final'), ('Initial State', 'Final State')):\n"
    '        image_path = path.with_name(path.stem + f\'_{stage}.png\')\n'
    '        ax.imshow(plt.imread(image_path))\n'
    "        ax.set_title(f\"{title}: {best[stage + '_objective']:.2f}\", fontsize=11)\n"
    "        ax.axis('off')\n"
    "    fig.suptitle(f\"{label} | Seed {run.seed} | Final {best['final_objective']:g}\", fontsize=13, fontweight='bold')\n"
    '    plt.tight_layout()\n'
    "    show(fig, f'09_states_{run.algo}.png')\n"
    "    print('Baseline kosong:', best['extra']['empty_baseline_used'], '| Kandidat feasible ditemukan:', best['extra']['found_feasible'])"
))
cells.append(md(
    '> ### Insights\n'
    '> Kualitas solusi dibaca dari fee dan feasibility, bukan hanya tampilan geladak yang rapat. '
    'Area kosong dapat muncul akibat kombinasi bentuk kendaraan dan kapasitas berat; gambar saja tidak memisahkan penyebab keduanya.'
))

cells.append(section('Multi-kapal dan Objective ETA', '10'))
cells.append(md(
    'Dua perluasan diuji tanpa mengubah variabel dasar persoalan: armada dengan beberapa kapal dan objective yang memberi '
    'bobot tambahan pada kendaraan ber-ETA kecil. Kedua eksperimen memakai kelompok hasil yang terpisah dari perbandingan utama.'
))
cells.append(md('## Penataan Armada'))
cells.append(md(
    'Objective armada menjumlahkan fee seluruh kapal, tetapi overlap dan kapasitas tetap diperiksa per geladak. '
    'Tabel berikut menampilkan pemanfaatan tiap kapal pada run multi-kapal dengan objective akhir tertinggi.'
))
cells.append(code(
    "multi_run, multi_best = max(of('multi'), key=lambda pair: pair[1]['final_objective'])\n"
    'multi_problem = problems[multi_run.instance]\n'
    "multi_state = State.from_dict(multi_problem, multi_best['final_state'])\n"
    'evaluation = multi_state.evaluate()\n'
    "table(['Kapal', 'Kendaraan', 'Berat', 'Kapasitas', 'Sel terisi', 'Luas'],\n"
    '      [[ship.id, sum(p is not None and p[0] == index for p in multi_state.positions),\n'
    '        evaluation.used_weight[index], ship.max_capacity, evaluation.occupied_cells[index], ship.area]\n'
    '       for index, ship in enumerate(multi_problem.ships)])\n\n'
    "for stage, title in (('initial', 'Initial State'), ('final', 'Final State')):\n"
    "    fig = draw_state(multi_problem, multi_best[stage + '_state'], title=f'{title}: Armada, Seed {multi_run.seed}')\n"
    "    show(fig, f'10_fleet_{stage}.png')\n\n"
    "insights(f\"Run multi terbaik memuat {multi_best['loaded']} kendaraan pada {len(multi_problem.ships)} kapal \"\n"
    "         f\"dengan objective {multi_best['final_objective']:.2f}. \"\n"
    "         'Nilainya tidak dibandingkan langsung dengan instance satu kapal karena kandidat dan kapasitasnya berbeda.')"
))
cells.append(md('## Objective Berbasis Urgensi ETA'))
cells.append(md(
    'Objective alternatif menggunakan `fee * (1 + 1/(eta + 1))`. Bobot urgensi bukan pendapatan uang. '
    'Pasangan run fee dan ETA pada seed yang sama dievaluasi kembali dengan kedua ukuran agar perubahan prioritas dapat dibaca dengan benar.'
))
cells.append(code(
    'eta_rows = []\n'
    "for eta_run, eta_result in of('eta'):\n"
    '    original = problems[eta_run.instance]\n'
    "    fee_run, fee_result = next((run, result) for run, result in of('sa') if run.seed == eta_run.seed)\n"
    '    assert fee_run.instance == eta_run.instance\n'
    "    assert fee_result['params'] == eta_result['params']\n"
    "    assert State.from_dict(original, fee_result['initial_state']).positions == State.from_dict(original, eta_result['initial_state']).positions\n"
    "    for mode, result in (('fee', fee_result), ('eta', eta_result)):\n"
    "        state = State.from_dict(original, result['final_state'])\n"
    '        loaded = [v for v, position in zip(original.vehicles, state.positions) if position is not None]\n'
    '        revenue = shipping_fee_total(original, state.positions)\n'
    '        urgency = sum(urgency_weight(vehicle) for vehicle in loaded)\n'
    '        mean_eta = mean(vehicle.eta for vehicle in loaded) if loaded else None\n'
    '        eta_rows.append([eta_run.seed, mode, revenue, urgency, len(loaded), mean_eta])\n'
    "table(['Seed', 'Objective pencarian', 'Fee asli', 'Bobot urgensi', 'Dimuat', 'Mean ETA (hari)'],\n"
    "      [[*row[:2], f'{row[2]:.2f}', f'{row[3]:.2f}', row[4], '-' if row[5] is None else f'{row[5]:.2f}'] for row in eta_rows])\n\n"
    "fee_mean = mean(row[2] for row in eta_rows if row[1] == 'fee')\n"
    "eta_fee_mean = mean(row[2] for row in eta_rows if row[1] == 'eta')\n"
    "fee_urgency = mean(row[3] for row in eta_rows if row[1] == 'fee')\n"
    "eta_urgency = mean(row[3] for row in eta_rows if row[1] == 'eta')\n"
    "insights(f'Perubahan mean dari objective fee ke ETA: pendapatan asli {eta_fee_mean - fee_mean:+.2f}; '\n"
    "         f'bobot urgensi {eta_urgency - fee_urgency:+.2f}. '\n"
    "         'Penempatan awal dan parameter berpasangan; yang diubah adalah nilai yang dioptimasi.')"
))
cells.append(md('## Visualisasi Hasil ETA'))
cells.append(md(
    'Run ETA terbaik ditampilkan dengan label bobot urgensi dan fee asli secara terpisah. '
    'Nilai pendapatan dihitung dari kendaraan yang benar-benar dimuat menggunakan fee pada input asli.'
))
cells.append(code(
    "eta_run, eta_best = max(of('eta'), key=lambda pair: pair[1]['final_objective'])\n"
    'original = problems[eta_run.instance]\n'
    'transformed = eta_problem(original)\n'
    "show(plot_run(eta_best), '11_eta_convergence.png')\n"
    "for stage, title in (('initial', 'Initial State'), ('final', 'Final State')):\n"
    "    state = State.from_dict(original, eta_best[stage + '_state'])\n"
    "    fig = draw_state(transformed, eta_best[stage + '_state'], title=f'{title}: ETA, Seed {eta_run.seed}',\n"
    "                     objective='eta', shipping_fee=shipping_fee_total(original, state.positions))\n"
    "    show(fig, f'11_eta_{stage}.png')"
))
cells.append(md(
    '> ### Insights\n'
    '> Field `total_fee` pada JSON ETA berisi bobot transformasi. Pendapatan aslinya berada pada '
    '`extra.shipping_fee_total`; kedua istilah tersebut tidak dapat dipertukarkan ketika membahas keuntungan pengiriman.'
))

cells.append(section('Batas Atas dan Optimum Eksak', '11'))
cells.append(md(
    'Relaksasi knapsack mengabaikan sebagian kendala geometri sehingga memberi upper bound. '
    'Instance kecil diselesaikan dengan branch-and-bound untuk menyediakan pembanding yang diketahui eksak.'
))
cells.append(md('## Verifikasi pada Instance Kecil'))
cells.append(md(
    'Nilai optimum dan susunan akhirnya dihitung langsung dari `small.json`. '
    'Pemeriksaan ini menunjukkan perbedaan antara batas atas dan optimum fisik; hasil instance kecil tidak membuktikan optimalitas pada instance utama.'
))
cells.append(code(
    "small = load_problem(CFG.DATA_DIR / 'small.json')\n"
    'exact = brute_force(small, max_nodes=CFG.EXACT_MAX_NODES)\n'
    'small_bound = upper_bound(small)\n'
    'assert exact.evaluate().is_feasible\n'
    'assert exact.objective <= small_bound + 1e-7\n'
    "table(['Instance', 'Optimum eksak', 'Upper bound', 'Selisih UB'],\n"
    '      [[small.name, exact.objective, small_bound, small_bound - exact.objective]])\n'
    "show(draw_state(small, exact.to_dict(), title='CARGO: Optimum Eksak pada Instance Kecil'), '12_exact_small.png')\n\n"
    "main_bound = of('hc')[0][1]['upper_bound']\n"
    "best_main = max(result['final_objective'] for results in compare.values() for result in results)\n"
    "insights(f'Instance kecil memiliki optimum {exact.objective:g} dan UB {small_bound:g}. '\n"
    "         f'Pada instance utama, solusi terbaik {best_main:g} dan UB {main_bound:g} membentuk batas bawah serta batas atas optimum. '\n"
    "         + ('Solusi feasible telah mencapai UB sehingga optimalitas terbukti.'\n"
    '            if math.isclose(best_main, main_bound, abs_tol=1e-7)\n'
    "            else 'Sisa gap dapat berasal dari relaksasi yang longgar, pencarian yang belum optimal, atau keduanya.'))"
))

cells.append(section('Pasca-Analisis', '12'))
cells.append(md(
    'Bagian akhir merangkum hasil kuantitatif serta batas interpretasi CARGO. '
    'Kesimpulan dibatasi pada instance, seed, dan budget yang dicatat dalam protokol.'
))
cells.append(md('## Ringkasan Temuan'))
cells.append(md(
    'Kualitas, kecepatan, dan konsistensi tidak harus menunjuk algoritma yang sama. '
    'Ringkasan berikut dihitung dari tabel perbandingan dan tidak menggunakan angka yang diketik ulang pada markdown.'
))
cells.append(code(
    "insights(f'Pada {len(pairs)} run resmi, mean kualitas tertinggi pada instance utama dicapai {best_quality[0]}; '\n"
    "         f'durasi mean terendah oleh {fastest[0]}; simpangan baku terendah oleh {consistent[0]}. '\n"
    "         f'Mean episode stuck checkpoint SA = {mean(result[\"extra\"][\"stuck_count\"] for result in sa_results):.2f}. '\n"
    "         'Perbandingan budget GA serta pasangan objective ETA memperlihatkan bahwa pemilihan konfigurasi perlu mempertimbangkan kualitas dan biaya.')"
))
cells.append(md(
    '### Kelebihan Pendekatan\n\n'
    'Representasi koordinat eksplisit membuat posisi, orientasi, dan kendaraan yang tidak dimuat dapat diperiksa langsung. '
    'Evaluator bersama menjaga definisi kendala tetap konsisten pada semua algoritma, sementara delta evaluation mengurangi '
    'pekerjaan evaluasi neighborhood. Pemisahan search dan analisis memungkinkan tabel serta gambar dibuat ulang dari JSON yang sama.\n\n'
    '---\n\n'
    '### Keterbatasan yang Diketahui\n\n'
    'Tiga seed memenuhi minimum eksperimen, tetapi belum cukup untuk klaim signifikansi statistik atau generalisasi ke semua input. '
    'Konfigurasi GA terbaik dipilih dari data eksperimen yang sama, bukan evaluasi hold-out. '
    'Monitoring SA hanya mengamati checkpoint dan menambah biaya yang sudah masuk durasi. '
    'Baseline kosong menjamin hasil fisik valid saat budget terlalu kecil, bukan keberhasilan menemukan muatan bernilai tinggi.\n\n'
    '---\n\n'
    '### Arah Pengembangan Berikutnya\n\n'
    'Eksperimen lanjutan dapat memperluas variasi ukuran geladak, distribusi dimensi, dan jumlah seed. '
    'Ablasi operator crossover, mutasi, dan aturan proposal diperlukan sebelum menyimpulkan penyebab perbedaan kualitas. '
    'Untuk pelaporan saat ini, seluruh pembandingan tetap menggunakan konfigurasi resmi yang tercatat tanpa menambahkan hasil sintetis.'
))

cells.append(section('Daftar Pustaka', '13'))
cells.append(md(
    'Tim Asisten Laboratorium Inteligensi Artifisial. (2026). *Spesifikasi Tugas Besar 1 IF3070 Dasar Inteligensi Artifisial 2026/2027*, versi 1.1.\n\n'
    'Tim Pengajar IF3070. (2026). *IF3070_Materi03-BeyondClassicalSearch*. Materi kuliah IF3070 Dasar Inteligensi Artifisial, Institut Teknologi Bandung.\n\n'
    'Kelompok G09 - Sepakat. (2026). *Laporan Tugas Besar 1 IF3070: CARGO*. [PDF](../docs/TugasBesar1_Sepakat.pdf).\n\n'
    'Project Jupyter. *NBClient: Executing Notebooks*. [Dokumentasi](https://nbclient.readthedocs.io/en/latest/client.html).'
))
cells.append(section('Thanks!', 'thanks'))
cells.append(md(
    '**Terima kasih kepada:**\n\n'
    'Dosen pengampu dan tim asisten IF3070 yang menyusun persoalan serta spesifikasi tugas. '
    'Seluruh anggota **G09 - Sepakat** bertanggung jawab memahami, memeriksa, dan menjelaskan implementasi serta hasil CARGO.'
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
