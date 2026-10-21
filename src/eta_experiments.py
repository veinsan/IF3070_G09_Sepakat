"""Run Bonus 1 (objective urgensi ETA): 3 run pada `main.json`, lalu bandingkan dengan run objective fee.

Contoh (dari root repo):

    python src/eta_experiments.py                # SA, seed 1, 2, 3 -> output/sa/main_eta_seed<k>.*
    python src/eta_experiments.py --no-plots     # tanpa gambar (lebih cepat)

Tiap run memakai `core.eta_objective.run_eta` dengan parameter default algoritma (config.py) dan disimpan
dengan `main.save_run`, jadi format JSON dan gambarnya sama dengan run lain. Nama file `main_eta_seed<k>`
sama dengan rencana grup `eta` di `experiments.py`.

Ringkasan perbandingan ditulis ke `output/summary_eta.md`: untuk seed yang sama, run objective fee
(`output/<algo>/main_seed<k>.json`, harus sudah ada) dibandingkan dengan run objective ETA dalam total fee asli,
total bobot urgensi, dan rata-rata ETA kendaraan yang dimuat.
"""

# Teks --help dan output terminal sengaja ASCII (lihat main.py).

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

from config import DEFAULT_INSTANCE, OUTPUT_DIR, SEEDS
from core.eta_objective import SUFFIX, eta_problem, run_eta, shipping_fee_total
from core.objective import evaluate
from core.problem import Problem, load_problem
from core.state import State
from main import ALGORITHMS, format_summary, run_id, save_run


def loaded_stats(problem: Problem, state: State) -> dict[str, float]:
    """Fee asli, bobot urgensi, banyak kendaraan, dan rata-rata ETA kendaraan yang dimuat di `state`."""
    positions = state.positions
    loaded = [v for v, p in zip(problem.vehicles, positions) if p is not None]
    return {
        "fee": shipping_fee_total(problem, positions),
        "urgency": evaluate(eta_problem(problem), positions).total_fee,
        "loaded": len(loaded),
        "mean_eta": statistics.mean(v.eta for v in loaded) if loaded else 0.0,
    }


def comparison(problem: Problem, algo: str, eta_results: list[dict[str, Any]], out_dir: Path) -> str:
    """Tabel Markdown: run objective fee vs objective ETA per seed (fee asli, bobot urgensi, ETA rata-rata)."""
    lines = [
        "# Ringkasan Bonus 1: objective urgensi ETA",
        "",
        f"Algoritma `{algo}`, instance `{problem.name}`, parameter default (`config.py`). Bobot urgensi "
        "w = fee * (1 + 1/(eta + 1)). Run fee dan run ETA dengan seed yang sama berangkat dari initial state yang "
        "sama.",
        "",
        "| Seed | Objective | Fee asli | Bobot urgensi | Dimuat | Mean ETA dimuat | Feasible | Gap UB |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for result in eta_results:
        fee_path = out_dir / algo / f"{run_id(result).replace(problem.name + SUFFIX, problem.name)}.json"
        rows = []
        if fee_path.is_file():
            rows.append(("fee", json.loads(fee_path.read_text(encoding="utf-8"))))
        rows.append(("eta", result))
        for kind, data in rows:
            stats = loaded_stats(problem, State.from_dict(problem, data["final_state"]))
            lines.append(
                f"| {data['seed']} | {kind} | {stats['fee']:g} | {stats['urgency']:.1f} | {stats['loaded']} | "
                f"{stats['mean_eta']:.2f} | {data['is_feasible']} | {100 * data['gap_ub']:.1f}% |"
            )
    lines.append("")
    lines.append("Gap UB tiap baris dihitung terhadap UB objective-nya sendiri (UB fee untuk run fee, UB bobot "
                 "untuk run ETA). Durasi tidak dibandingkan di sini karena run fee resmi dijalankan "
                 "pada kondisi mesin yang lain (EXPERIMENTS §4); durasi tiap run ada di JSON-nya.")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--algo", choices=sorted(ALGORITHMS), default="sa")
    parser.add_argument("--instance", type=Path, default=DEFAULT_INSTANCE)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(SEEDS))
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args(argv)

    problem = load_problem(args.instance)
    function = ALGORITHMS[args.algo][0]
    results = []
    for seed in args.seeds:
        run = run_eta(function, problem, seed=seed)
        result = run.to_dict()
        path = save_run(result, run.problem, args.out, plots=not args.no_plots)[0]
        print(format_summary(result))
        print(f"disimpan    : {path}\n")
        results.append(result)

    summary = args.out / "summary_eta.md"
    summary.write_text(comparison(problem, args.algo, results, args.out), encoding="utf-8")
    print(f"ringkasan   : {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
