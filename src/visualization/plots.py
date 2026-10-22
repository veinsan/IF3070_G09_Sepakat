"""Plot hasil eksperimen dari dict hasil run (`RunResult.to_dict()`, EXPERIMENTS §3).

Plot wajib menurut spesifikasi (bagian Cakupan) dan sumber datanya:

| Plot                                   | Algoritma         | Data                                   |
|----------------------------------------|-------------------|----------------------------------------|
| Objective vs iterasi                   | semua             | `history["objective"]`                 |
| Objective terbaik sejauh ini           | Random Restart HC | `history["best"]`                      |
| e^(ΔE/T) vs iterasi                    | SA                | `history["prob"]` = `[iterasi, nilai]` |
| Objective maksimum dan rata-rata       | GA                | `history["objective"]`, `history["mean"]` |

Fungsi menerima dict (bukan `RunResult`) supaya plot bisa dibuat langsung dari file JSON di `output/` tanpa
memuat instance atau menjalankan search lagi. Memakai `matplotlib.figure.Figure` tanpa pyplot.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from statistics import mean
from typing import Any

from matplotlib.figure import Figure

Result = dict[str, Any]


def run_label(result: Result) -> str:
    """Label singkat satu run, misalnya `steepest | main | seed 1`."""
    return f"{result['algorithm']} | {result['instance']} | seed {result['seed']}"


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
    feasible = history.get("best_feasible")
    if feasible is not None and feasible != objective and feasible != history.get("best"):
        ax.plot(range(len(feasible)), feasible, linewidth=1.4, linestyle="-.",
                label="terbaik feasible")
    if result.get("upper_bound") is not None:
        ax.axhline(result["upper_bound"], color="gray", linewidth=0.8, linestyle=":",
                   label=f"upper bound ({result['upper_bound']:g})")
    ax.set_xlabel("generasi" if is_population else "iterasi")
    ax.set_ylabel("objective (bobot urgensi)" if result.get("extra", {}).get("objective") == "eta" else "objective")
    ax.set_title(f"Objective vs {'generasi' if is_population else 'iterasi'} | awal {result['initial_objective']:g}"
                 f" → akhir {result['final_objective']:g}", fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)


def plot_acceptance(ax, result: Result) -> None:
    """Peluang menerima move yang lebih buruk, e^(ΔE/T), vs iterasi (SA, hanya iterasi dengan ΔE < 0)."""
    pairs = result["history"]["prob"]
    ax.scatter([p[0] for p in pairs], [p[1] for p in pairs], s=1, alpha=0.3, linewidths=0)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("iterasi")
    ax.set_ylabel("e^(ΔE/T)")
    stuck = result.get("extra", {}).get("stuck_count")
    ax.set_title("e^(ΔE/T) vs iterasi" + (f" | stuck {stuck} kali" if stuck is not None else ""), fontsize=9)
    ax.grid(alpha=0.3)


def plot_run(result: Result, path: str | Path | None = None) -> Figure:
    """Semua plot satu run dalam satu Figure: objective, ditambah e^(ΔE/T) bila ada (SA). Disimpan bila `path`."""
    has_prob = "prob" in result["history"]
    fig = Figure(figsize=(11 if has_prob else 7, 4), layout="constrained")
    axes = fig.subplots(1, 2 if has_prob else 1, squeeze=False)[0]
    plot_objective(axes[0], result)
    if has_prob:
        plot_acceptance(axes[1], result)
    fig.suptitle(f"{run_label(result)} | {result['iterations']} iterasi | {result['duration_s']:.2f} s")
    if path is not None:
        _save(fig, path)
    return fig


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


def _save(fig: Figure, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150)
