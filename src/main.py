"""CLI: jalankan satu algoritma local search pada satu instance, lalu simpan hasilnya ke `output/`.

Contoh (dari root repo):

    python src/main.py --algo hc --seed 1
    python src/main.py --algo sa --instance multi.json --seed 2
    python src/main.py --algo ga --population 50 --iterations 300 --seed 3
    python src/main.py --view output/sa/main_seed1.json

Hasil satu run disimpan ke `<out>/<algo>/<run_id>.json` (dict `RunResult.to_dict()`, EXPERIMENTS §2) beserta
`<run_id>_initial.png`, `<run_id>_final.png` (state awal/akhir), dan `<run_id>_plot.png` (plot objective, dan
e^(dE/T) untuk SA). `run_id` = `<instance>_seed<seed>`, untuk GA `<instance>_pop<P>_iter<I>_seed<seed>`.

Fungsi `run_algorithm`, `run_id`, `save_run`, dan `format_summary` dipakai juga oleh `experiments.py`.
"""

# Docstring ini juga teks --help dan semua output terminal sengaja ASCII: konsol Windows yang di-redirect
# memakai encoding cp1252 yang tidak bisa mencetak karakter seperti Δ.

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from config import DATA_DIR, DEFAULT_INSTANCE, OUTPUT_DIR
from core.eta_objective import SUFFIX, eta_problem
from core.problem import Problem, load_problem
from search.genetic_algorithm import genetic_algorithm
from search.hill_climbing import random_restart, sideways_move, steepest_ascent, stochastic
from search.result import RunResult
from search.simulated_annealing import simulated_annealing

# nama algoritma di CLI -> (fungsi, {opsi CLI: nama parameter fungsi}). Parameter yang tidak diberikan
# memakai default fungsi, yaitu nilai di config.py.
ALGORITHMS: dict[str, tuple[Callable[..., RunResult], dict[str, str]]] = {
    "steepest": (steepest_ascent, {"max_iterations": "max_iterations"}),
    "sideways": (sideways_move, {"max_sideways": "max_sideways", "max_iterations": "max_iterations"}),
    "random_restart": (random_restart, {"max_restart": "max_restart", "max_iterations": "max_iterations"}),
    "stochastic": (stochastic, {"max_no_improve": "max_no_improve", "max_iterations": "max_iterations"}),
    "sa": (simulated_annealing, {"iterations": "iterations"}),
    "ga": (genetic_algorithm, {"population": "population_size", "iterations": "iterations"}),
}
ALIASES = {"hc": "steepest"}

# objective yang dioptimasi lewat CLI. Run Bonus 1 (objective ETA) dibuat oleh `eta_experiments.py` atau grup
# `eta` di `experiments.py`; hasilnya tetap bisa dibuka dengan --view (`view_problem`).
OBJECTIVES = ("fee",)

PARAM_OPTIONS = ("max_sideways", "max_restart", "max_no_improve", "max_iterations", "iterations", "population")


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


def save_run(result: dict[str, Any], problem: Problem, out_dir: str | Path = OUTPUT_DIR,
             plots: bool = True) -> list[Path]:
    """Simpan JSON hasil run ke `<out_dir>/<algo>/<run_id>.json`, plus gambar state dan plot bila `plots`.

    Mengembalikan daftar file yang ditulis. `duration_s` di JSON tetap durasi search dari algoritma, tidak
    termasuk waktu menyimpan file dan gambar.
    """
    prefix = Path(out_dir) / result["algorithm"] / run_id(result)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    path = prefix.with_suffix(".json")
    # tanpa indentasi: history SA berisi ~100 000 titik
    path.write_text(json.dumps(result) + "\n", encoding="utf-8")
    return [path] + (save_plots(result, problem, prefix) if plots else [])


def save_plots(result: dict[str, Any], problem: Problem, prefix: Path) -> list[Path]:
    """Gambar state awal/akhir dan plot run ke `<prefix>_initial.png`, `_final.png`, `_plot.png`."""
    # import di sini supaya run tanpa gambar tidak perlu memuat matplotlib
    from visualization.plots import plot_run
    from visualization.state_view import save_run_states

    paths = save_run_states(problem, result, prefix)
    plot_path = prefix.with_name(f"{prefix.name}_plot.png")
    plot_run(result, plot_path)
    return paths + [plot_path]


def format_summary(result: dict[str, Any]) -> str:
    """Ringkasan satu run untuk terminal: parameter, objective, feasibility, gap ke UB, iterasi, durasi."""
    violations = result["violations"]
    weight = ", ".join(f"{u:g}/{c:g}" for u, c in zip(result["used_weight"], result["capacity"]))
    lines = [
        f"algoritma   : {result['algorithm']} | instance {result['instance']} | seed {result['seed']}",
        f"parameter   : {json.dumps(result['params'])}",
        f"objective   : awal {result['initial_objective']:g} -> akhir {result['final_objective']:g}",
        f"total fee   : {result['total_fee']:g} | upper bound {result['upper_bound']:g} | "
        f"gap {100 * result['gap_ub']:.2f}%",
        f"feasible    : {result['is_feasible']} (overlap {violations['overlap_cells']}, keluar batas "
        f"{violations['out_of_bound_cells']}, kelebihan berat {violations['weight_units']})",
        f"muatan      : {result['loaded']} kendaraan | berat {weight} | luas terpakai "
        f"{result['used_area_pct']:.1f}%",
        f"iterasi     : {result['iterations']} | evaluasi {result['evaluations']} | "
        f"durasi {result['duration_s']:.3f} s",
    ]
    # info khusus algoritma (restart, sideways, stuck, T0, ...); list panjang tidak ditampilkan
    extra = {k: v for k, v in result["extra"].items() if isinstance(v, (int, float, str))}
    if extra:
        lines.append("info        : " + ", ".join(f"{k}={v:g}" if isinstance(v, float) else f"{k}={v}"
                                                   for k, v in extra.items()))
    return "\n".join(lines)


def resolve_instance(value: str) -> Path:
    """Path instance: path apa adanya bila ada, selain itu dicari di `src/data/` (`multi.json` atau `multi`)."""
    path = Path(value)
    if path.is_file():
        return path
    for candidate in (DATA_DIR / value, DATA_DIR / f"{value}.json"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"instance '{value}' tidak ditemukan (cek path atau nama file di {DATA_DIR})")


def view_problem(result: dict[str, Any], instance: str | None = None) -> Problem:
    """Instance untuk --view: `instance` bila diberikan, selain itu dari hasil run. Hasil run Bonus 1 (instance
    `<nama>_eta`) memakai instance turunan bobot urgensi, sama seperti saat run-nya dijalankan."""
    name = instance or result["instance"]
    if instance is None and name.endswith(SUFFIX):
        return eta_problem(load_problem(resolve_instance(name.removesuffix(SUFFIX))))
    return load_problem(resolve_instance(name))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--algo", choices=[*ALGORITHMS, *ALIASES],
                        help="algoritma (hc = steepest). Wajib kecuali memakai --view")
    parser.add_argument("--instance", help=f"file instance JSON (default {DEFAULT_INSTANCE.name}); nama "
                                           "file di src/data/ juga diterima, misalnya multi.json")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--objective", choices=OBJECTIVES, default="fee",
                        help="objective yang dioptimasi (ETA, Bonus 1, belum tersedia)")
    params = parser.add_argument_group("parameter algoritma (default: config.py)")
    params.add_argument("--max-sideways", type=int, help="sideways")
    params.add_argument("--max-restart", type=int, help="random_restart")
    params.add_argument("--max-no-improve", type=int, help="stochastic")
    params.add_argument("--max-iterations", type=int,
                        help="batas pengaman iterasi semua varian HC (per percobaan untuk random_restart)")
    params.add_argument("--iterations", type=int, help="sa (iterasi), ga (generasi)")
    params.add_argument("--population", type=int, help="ga")
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR, help="folder output (default output/)")
    parser.add_argument("--no-save", action="store_true", help="hanya tampilkan hasil, tidak menulis file")
    parser.add_argument("--no-plot", action="store_true", help="simpan JSON saja, tanpa gambar")
    parser.add_argument("--view", type=Path, metavar="JSON",
                        help="tampilkan dan gambar ulang hasil run yang sudah disimpan, tanpa menjalankan search")
    return parser


def main(argv: list[str] | None = None) -> int:
    from visualization.state_view import render_state_text

    parser = build_parser()
    args = parser.parse_args(argv)
    given = {k: getattr(args, k) for k in PARAM_OPTIONS if getattr(args, k) is not None}

    if args.view is not None:
        if args.algo is not None or given:
            parser.error("--view tidak bisa digabung dengan --algo atau parameter algoritma")
        try:
            result = json.loads(args.view.read_text(encoding="utf-8"))
            problem = view_problem(result, args.instance)
            # validasi: hasil run harus cocok dengan instance-nya
            RunResult.from_dict(problem, result)
        except (OSError, ValueError, KeyError) as e:
            parser.error(f"--view {args.view}: {e}")
        print(format_summary(result))
        print()
        print(render_state_text(problem, result["final_state"]))
        if not args.no_plot:
            paths = save_plots(result, problem, args.view.with_suffix(""))
            print("\ngambar:", *paths, sep="\n  ")
        return 0

    if args.algo is None:
        parser.error("--algo wajib diisi (atau pakai --view)")
    algo = ALIASES.get(args.algo, args.algo)
    invalid = set(given) - set(ALGORITHMS[algo][1])
    if invalid:
        options = ", ".join("--" + k.replace("_", "-") for k in sorted(invalid))
        parser.error(f"{options} tidak berlaku untuk algoritma {algo}")
    for k, v in given.items():
        if v < (0 if k.startswith("max_") else 1):
            parser.error(f"--{k.replace('_', '-')} tidak boleh {v}")
    try:
        problem = load_problem(resolve_instance(args.instance or str(DEFAULT_INSTANCE)))
    except (OSError, ValueError) as e:
        parser.error(str(e))

    result = run_algorithm(algo, problem, args.seed, **given).to_dict()
    print(format_summary(result))
    print()
    print(render_state_text(problem, result["final_state"]))
    if not args.no_save:
        paths = save_run(result, problem, args.out, plots=not args.no_plot)
        print("\ndisimpan:", *paths, sep="\n  ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
