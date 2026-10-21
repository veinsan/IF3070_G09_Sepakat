"""Runner eksperimen: jalankan semua run di EXPERIMENTS §3-§4, simpan ke `output/`, lalu tulis ringkasan.

Contoh (dari root repo):

    python src/experiments.py --dry-run          # daftar run tanpa menjalankan
    python src/experiments.py                    # semua run -> output/ + output/summary.md
    python src/experiments.py --only sa ga_pop   # sebagian grup saja
    python src/experiments.py --skip-existing    # lanjutkan run yang terputus
    python src/experiments.py --plots-only       # gambar ulang + ringkasan dari JSON yang sudah ada

Tiap run dijalankan dan disimpan dengan fungsi yang sama dengan CLI (`main.run_algorithm`, `main.save_run`),
jadi hasilnya identik dengan `python src/main.py --algo <algo> --instance <instance> --seed <seed> ...`.

Grup run (seed 1, 2, 3, parameter dari config.py):

| Grup          | EXPERIMENTS | Isi                                                            | Run |
|---------------|-------------|----------------------------------------------------------------|-----|
| `hc`          | §4.1        | Steepest Ascent                                                | 3   |
| `sa`          | §4.5        | Simulated Annealing                                            | 3   |
| `ga_iter`     | §4.6        | GA populasi kontrol, variasi iterasi                           | 9   |
| `ga_pop`      | §4.7        | GA iterasi kontrol, variasi populasi                           | 9   |
| `hc_variants` | §4.2-§4.4   | Stochastic, Sideways Move, Random Restart (Bonus 2)            | 9   |
| `eta`         | §4.10       | SA dengan objective urgensi ETA (Bonus 1, `core.eta_objective`) | 3   |
| `multi`       | §4.8        | Steepest Ascent pada `multi.json` (Bonus 3)                    | 3   |

Konfigurasi kontrol GA (populasi 100, iterasi 1000) masuk ke `ga_iter` dan `ga_pop` tetapi hanya dijalankan
sekali, sehingga totalnya 21 run wajib dan 36 run dengan bonus.

Run Bonus 1 dijalankan dengan `core.eta_objective.run_eta`, sama seperti `src/eta_experiments.py`, jadi file
`output/sa/main_eta_seed<k>.json` dari kedua runner identik. Perbandingan run fee vs ETA tetap ditulis oleh
`eta_experiments.py` ke `output/summary_eta.md`.

`--quick` memakai `small.json` dan parameter kecil (dipakai test). Hasilnya tetap ke `--out`, jadi pakai
folder lain dari `output/` supaya tidak tercampur dengan hasil resmi.
"""

# Teks --help dan output terminal sengaja ASCII (lihat main.py).

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Any

from config import (
    DEFAULT_INSTANCE,
    GA_ITERATION_VARIANTS,
    GA_ITERATIONS,
    GA_POPULATION,
    GA_POPULATION_VARIANTS,
    MULTI_INSTANCE,
    OUTPUT_DIR,
    SEEDS,
)
from core.eta_objective import eta_problem, run_eta
from core.problem import Problem, load_problem
from main import resolve_instance, run_algorithm, run_id, save_plots, save_run
from search.result import RunResult

Result = dict[str, Any]

# grup -> (judul di ringkasan, wajib?)
GROUPS: dict[str, tuple[str, bool]] = {
    "hc": ("4.1 Hill-Climbing - Steepest Ascent", True),
    "sa": ("4.5 Simulated Annealing", True),
    "ga_iter": ("4.6 GA - kontrol populasi, variasi iterasi", True),
    "ga_pop": ("4.7 GA - kontrol iterasi, variasi populasi", True),
    "hc_variants": ("4.2-4.4 Hill-Climbing varian lain (Bonus 2)", False),
    "eta": ("4.10 Bonus 1 - objective urgensi ETA", False),
    "multi": ("4.8 Bonus 3 - multi-kapal", False),
}


@dataclass
class Run:
    """Satu run yang direncanakan. `params` memakai nama opsi CLI (`population`, `max_restart`, ...)."""

    groups: tuple[str, ...]
    algo: str
    instance: Path
    seed: int
    params: dict[str, int] = field(default_factory=dict)
    objective: str = "fee"

    @property
    def run_id(self) -> str:
        params = {"population": self.params.get("population"), "iterations": self.params.get("iterations")}
        name = run_id({"algorithm": self.algo, "instance": self.instance.stem, "seed": self.seed, "params": params})
        # run Bonus 1 dibedakan dari run fee biasa supaya file tidak saling menimpa
        return name if self.objective == "fee" else name.replace("_seed", f"_{self.objective}_seed")

    @property
    def required(self) -> bool:
        return any(GROUPS[g][1] for g in self.groups)

    def path(self, out_dir: Path) -> Path:
        return Path(out_dir) / self.algo / f"{self.run_id}.json"


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


def select(runs: Sequence[Run], only: Sequence[str] | None) -> list[Run]:
    """Run yang termasuk salah satu grup di `only` (semua bila `only` kosong)."""
    return [r for r in runs if not only or set(r.groups) & set(only)]


def count_line(runs: Sequence[Run]) -> str:
    return f"{sum(r.required for r in runs)} run wajib, {len(runs)} run dengan bonus"


def describe(run: Run, out_dir: Path, skip_existing: bool) -> str:
    if skip_existing and run.path(out_dir).is_file():
        status = "sudah ada"
    else:
        status = "dijalankan"
    params = " ".join(f"{k}={v}" for k, v in run.params.items())
    return f"{','.join(run.groups):<16} {run.algo:<15} {run.instance.name:<11} {run.run_id:<28} {params:<30} {status}"


def problem_for(run: Run, problems: dict[Path, Problem]) -> Problem:
    """Instance yang dioptimasi `run`: instance asli, atau turunan bobot urgensi untuk objective ETA."""
    problem = problems.setdefault(run.instance, load_problem(run.instance))
    return eta_problem(problem) if run.objective == "eta" else problem


def search(run: Run, problem: Problem) -> RunResult:
    """Jalankan `run` pada instance asli `problem` (run ETA lewat `run_eta`, seperti eta_experiments.py)."""
    if run.objective == "eta":
        return run_eta(partial(run_algorithm, run.algo), problem, seed=run.seed, **run.params)
    return run_algorithm(run.algo, problem, run.seed, **run.params)


def execute(runs: Sequence[Run], out_dir: Path, skip_existing: bool = False, plots: bool = True,
            log: Callable[[str], None] = print) -> list[Path]:
    """Jalankan dan simpan `runs` (lewat `main.run_algorithm` / `main.save_run`). Mengembalikan JSON yang ditulis."""
    problems: dict[Path, Problem] = {}
    written = []
    for k, run in enumerate(runs, start=1):
        head = f"[{k}/{len(runs)}] {run.algo} {run.run_id}"
        if skip_existing and run.path(out_dir).is_file():
            log(f"{head}: sudah ada, dilewati")
            continue
        problems.setdefault(run.instance, load_problem(run.instance))
        run_result = search(run, problems[run.instance])
        result = run_result.to_dict()
        written.append(save_run(result, run_result.problem, out_dir, plots=plots)[0])
        log(f"{head}: objective {result['initial_objective']:g} -> {result['final_objective']:g}, "
            f"feasible {result['is_feasible']}, {result['duration_s']:.2f} s")
    return written


def redraw(runs: Sequence[Run], out_dir: Path, log: Callable[[str], None] = print) -> int:
    """Gambar ulang state dan plot dari JSON yang sudah ada, tanpa menjalankan search. Mengembalikan jumlahnya."""
    problems: dict[Path, Problem] = {}
    count = 0
    for run in runs:
        path = run.path(out_dir)
        if not path.is_file():
            continue
        save_plots(load_result(path), problem_for(run, problems), path.with_suffix(""))
        count += 1
        log(f"gambar ulang {path}")
    return count


def load_result(path: Path) -> Result:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_results(runs: Sequence[Run], out_dir: Path) -> list[tuple[Run, Result]]:
    """Pasangan (run, hasil) untuk semua run yang JSON-nya sudah ada di `out_dir`."""
    return [(r, load_result(r.path(out_dir))) for r in runs if r.path(out_dir).is_file()]


# --- ringkasan ---------------------------------------------------------------------------------------


def machine_info() -> str:
    return (f"{platform.platform()} | CPU {platform.processor() or platform.machine()} ({os.cpu_count()} thread) | "
            f"Python {platform.python_version()}")


def _num(value: float) -> str:
    return f"{value:g}"


def _mean_std(values: Sequence[float], digits: int = 1) -> str:
    if not values:
        return ""
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    return f"{statistics.mean(values):.{digits}f} ± {std:.{digits}f}"


def _gap(result: Result) -> str:
    return f"{100 * result['gap_ub']:.1f}%"


def _table(header: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    return ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)] + [
        "| " + " | ".join(str(c) for c in row) + " |" for row in rows
    ]


def _seed_rows(results: Sequence[Result], columns: Callable[[Result], list[Any]]) -> list[list[Any]]:
    return [[k, r["seed"], *columns(r)] for k, r in enumerate(sorted(results, key=lambda r: r["seed"]), start=1)]


def _ga_rows(results: Sequence[Result], key: str) -> list[list[Any]]:
    rows = []
    for value in sorted({r["params"][key] for r in results}):
        group = sorted((r for r in results if r["params"][key] == value), key=lambda r: r["seed"])
        rows.append([
            value, f"1-{len(group)}", ",".join(str(r["seed"]) for r in group),
            " / ".join(_num(r["final_objective"]) for r in group) + f" (mean {_mean_std([r['final_objective'] for r in group])})",
            " / ".join(_num(r["total_fee"]) for r in group),
            " / ".join(str(r["is_feasible"]) for r in group),
            " / ".join(_gap(r) for r in group),
            " / ".join(f"{r['duration_s']:.3f}" for r in group),
        ])
    return rows


def summary_sections(pairs: Sequence[tuple[Run, Result]]) -> list[str]:
    """Tabel markdown dengan kolom yang sama seperti EXPERIMENTS §4, siap disalin ke dokumen."""

    def of(group: str, algo: str | None = None) -> list[Result]:
        return [res for run, res in pairs if group in run.groups and (algo is None or run.algo == algo)]

    def basic(r: Result) -> list[Any]:
        return [_num(r["initial_objective"]), _num(r["final_objective"]), _num(r["total_fee"]), r["is_feasible"],
                _gap(r)]

    lines: list[str] = []

    def section(title: str, header: list[str], rows: list[list[Any]], results: Sequence[Result],
                mean_columns: dict[int, Callable[[Result], float]] | None = None) -> None:
        if not results:
            return
        if mean_columns:
            row: list[Any] = ["**mean ± std**", ""] + [""] * (len(header) - 2)
            for column, value in mean_columns.items():
                row[column] = _mean_std([value(r) for r in results], 3 if column == len(header) - 1 else 1)
            rows = rows + [row]
        lines.extend(["", f"### {title}", ""] + _table(header, rows))

    head = ["Run", "Seed", "Obj awal", "Obj akhir", "Fee", "Feasible", "Gap UB"]
    final_mean = {3: lambda r: r["final_objective"], 4: lambda r: r["total_fee"]}

    hc = of("hc")
    section(GROUPS["hc"][0], head + ["Iterasi", "Evals", "Durasi (s)"], _seed_rows(
        hc, lambda r: basic(r) + [r["iterations"], r["evaluations"], f"{r['duration_s']:.3f}"]), hc,
        {**final_mean, 9: lambda r: r["duration_s"]})
    stochastic = of("hc_variants", "stochastic")
    section("4.2 Hill-Climbing - Stochastic (Bonus 2)", head + ["Iterasi", "Evals", "Durasi (s)"], _seed_rows(
        stochastic, lambda r: basic(r) + [r["iterations"], r["evaluations"], f"{r['duration_s']:.3f}"]), stochastic,
        {**final_mean, 9: lambda r: r["duration_s"]})
    sideways = of("hc_variants", "sideways")
    section("4.3 Hill-Climbing - Sideways Move", head + ["Iterasi", "#Sideways", "Durasi (s)"], _seed_rows(
        sideways, lambda r: basic(r) + [r["iterations"], r["extra"].get("sideways_moves", ""),
                                        f"{r['duration_s']:.3f}"]), sideways,
        {**final_mean, 9: lambda r: r["duration_s"]})
    restart = of("hc_variants", "random_restart")
    section("4.4 Hill-Climbing - Random Restart",
            ["Run", "Seed", "Obj akhir", "Fee", "Feasible", "Gap UB", "#Restart", "Iterasi per restart",
             "Durasi (s)"],
            _seed_rows(restart, lambda r: basic(r)[1:] + [
                r["extra"].get("restarts", ""), ", ".join(str(i) for i in r["extra"].get("iters_per_restart", [])),
                f"{r['duration_s']:.3f}"]), restart,
            {2: lambda r: r["final_objective"], 3: lambda r: r["total_fee"], 8: lambda r: r["duration_s"]})
    sa = of("sa")
    section(GROUPS["sa"][0], head + ["Iterasi", "#Stuck", "Durasi (s)"], _seed_rows(
        sa, lambda r: basic(r) + [r["iterations"], r["extra"].get("stuck_count", ""), f"{r['duration_s']:.3f}"]),
        sa, {**final_mean, 9: lambda r: r["duration_s"]})
    ga_head = ["Obj akhir (best)", "Fee", "Feasible", "Gap UB", "Durasi (s)"]
    section(GROUPS["ga_iter"][0], ["Iterasi", "Run", "Seed"] + ga_head, _ga_rows(of("ga_iter"), "iterations"),
            of("ga_iter"))
    section(GROUPS["ga_pop"][0], ["Populasi", "Run", "Seed"] + ga_head, _ga_rows(of("ga_pop"), "population"),
            of("ga_pop"))
    multi = of("multi")
    section(GROUPS["multi"][0], head + ["Berat per kapal", "Kendaraan per kapal", "Durasi (s)"], _seed_rows(
        multi, lambda r: basic(r) + [
            " / ".join(f"{u:g}/{c:g}" for u, c in zip(r["used_weight"], r["capacity"])),
            " / ".join(str(n) for n in vehicles_per_ship(r)), f"{r['duration_s']:.3f}"]), multi,
        {**final_mean, 9: lambda r: r["duration_s"]})
    overview = []
    for label, results in comparison_groups(pairs).items():
        finals = [r["final_objective"] for r in results]
        overview.append([label, _num(max(finals)), _mean_std(finals),
                         f"{100 * statistics.mean(r['gap_ub'] for r in results):.1f}%",
                         f"{statistics.mean(r['duration_s'] for r in results):.3f}",
                         f"{statistics.mean(r['evaluations'] for r in results):.0f}"])
    if overview:
        lines.extend(["", "### 4.9 Ringkasan antar-algoritma (instance utama)", ""] + _table(
            ["Algoritma", "Best", "Mean ± std", "Gap UB (mean)", "Durasi mean (s)", "Evals mean"], overview))

    eta = of("eta")
    section(GROUPS["eta"][0],
            ["Run", "Seed", "Obj awal", "Obj akhir (bobot)", "Fee asli", "Feasible", "Gap UB", "Dimuat", "Berat",
             "Iterasi", "#Stuck", "Durasi (s)"],
            _seed_rows(eta, lambda r: [
                _num(round(r["initial_objective"], 1)), _num(round(r["final_objective"], 1)),
                _num(r["extra"]["shipping_fee_total"]), r["is_feasible"], _gap(r), r["loaded"],
                " / ".join(f"{u:g}/{c:g}" for u, c in zip(r["used_weight"], r["capacity"])), r["iterations"],
                r["extra"].get("stuck_count", ""), f"{r['duration_s']:.3f}"]), eta,
            {3: lambda r: r["final_objective"], 4: lambda r: r["extra"]["shipping_fee_total"],
             11: lambda r: r["duration_s"]})
    if eta:
        lines.extend(["", "Bobot urgensi `fee * (1 + 1/(eta + 1))`, gap terhadap UB bobot. Perbandingan dengan run "
                      "objective fee pada seed yang sama: `output/summary_eta.md`."])
    return lines


def vehicles_per_ship(result: Result) -> list[int]:
    """Banyak kendaraan di tiap kapal pada final state."""
    counts = [0] * len(result["capacity"])
    ship_index = {deck["id"]: s for s, deck in enumerate(result["final_state"]["decks"])}
    for vehicle in result["final_state"]["vehicles"]:
        if vehicle["ship"] is not None:
            counts[ship_index[vehicle["ship"]]] += 1
    return counts


def comparison_groups(pairs: Sequence[tuple[Run, Result]]) -> dict[str, list[Result]]:
    """Run objective fee di instance utama per algoritma; GA diwakili konfigurasi dengan mean objective terbaik."""
    groups: dict[str, list[Result]] = {}
    ga: dict[str, list[Result]] = {}
    for run, result in pairs:
        if run.objective != "fee" or "multi" in run.groups:
            continue
        if run.algo == "ga":
            ga.setdefault(f"ga (pop {run.params['population']}, iter {run.params['iterations']})", []).append(result)
        else:
            groups.setdefault(run.algo, []).append(result)
    if ga:
        best = max(ga, key=lambda k: statistics.mean(r["final_objective"] for r in ga[k]))
        groups[best + " - terbaik"] = ga[best]
    return groups


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


# --- CLI ---------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="+", choices=list(GROUPS), metavar="GRUP",
                        help=f"hanya grup ini ({', '.join(GROUPS)})")
    parser.add_argument("--skip-existing", action="store_true", help="lewati run yang JSON-nya sudah ada")
    parser.add_argument("--dry-run", action="store_true", help="tampilkan daftar run tanpa menjalankan")
    parser.add_argument("--plots-only", action="store_true",
                        help="tanpa search: gambar ulang semua run dari JSON yang ada, lalu tulis ringkasan")
    parser.add_argument("--quick", action="store_true", help="small.json + parameter kecil (uji coba / test)")
    parser.add_argument("--no-plot", action="store_true", help="simpan JSON dan summary.md saja, tanpa gambar")
    parser.add_argument("--out", type=Path, default=OUTPUT_DIR, help="folder output (default output/)")
    args = parser.parse_args(argv)
    if args.dry_run and args.plots_only:
        parser.error("--dry-run tidak bisa digabung dengan --plots-only")

    runs = select(planned_runs(quick=args.quick), args.only)
    print(f"Rencana: {count_line(runs)} -> {args.out}")
    if args.dry_run:
        for run in runs:
            print("  " + describe(run, args.out, args.skip_existing))
        return 0

    start = time.perf_counter()
    if args.plots_only:
        print(f"{redraw(runs, args.out)} run digambar ulang")
    else:
        execute(runs, args.out, skip_existing=args.skip_existing, plots=not args.no_plot)

    # ringkasan selalu mencakup semua run yang direncanakan (bukan hanya --only) yang JSON-nya sudah ada
    everything = planned_runs(quick=args.quick)
    pairs = load_results(everything, args.out)
    missing = [r for r in everything if not r.path(args.out).is_file()]
    path = write_summary(pairs, args.out, missing, plots=not args.no_plot)
    print(f"Ringkasan: {path} ({len(pairs)} run) | total waktu {time.perf_counter() - start:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
