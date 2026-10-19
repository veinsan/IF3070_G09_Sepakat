"""Visualisasi satu state: keadaan tiap geladak, kendaraan di dalam dan di luar kapal, serta value-nya.

Spesifikasi meminta state dan visualisasi menunjukkan (1) keadaan semua kendaraan di dalam maupun di luar,
(2) keadaan geladak kapal, dan (3) value state tersebut. Modul ini menggambar ketiganya dari dict state hasil
`State.to_dict()` (field `initial_state` / `final_state` di JSON hasil run, EXPERIMENTS §2), sehingga gambar
bisa dibuat ulang dari `output/` tanpa menjalankan search lagi (DESIGN §10).

- `draw_state`        : satu Figure matplotlib, satu panel per kapal (multi-kapal, Bonus 3) + daftar kendaraan
                        di luar kapal. Sel overlap diarsir merah, bagian kendaraan yang keluar geladak digambar
                        putus-putus merah.
- `render_state_text` : versi teks (ASCII) untuk terminal dan demo.
- `save_run_states`   : simpan `<prefix>_initial.png` dan `<prefix>_final.png` dari dict hasil run.

Memakai `matplotlib.figure.Figure` langsung (tanpa pyplot), jadi tidak butuh GUI backend dan tidak ada state
global matplotlib yang tertinggal.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from matplotlib import colormaps
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from core.objective import dimensions
from core.problem import Problem
from core.state import State

# ukuran satu sel grid di gambar (inci) dan lebar panel daftar kendaraan di luar kapal (dalam satuan sel)
CELL_INCH = 0.42
OUTSIDE_PANEL_CELLS = 9
# 60 warna yang cukup berbeda; kendaraan ke-i selalu memakai warna yang sama di semua gambar
PALETTE = [colormaps[name](k) for name in ("tab20", "tab20b", "tab20c") for k in range(20)]
VIOLATION_COLOR = "#d62728"


def vehicle_color(i: int) -> tuple[float, float, float, float]:
    """Warna tetap untuk kendaraan dengan index `i`."""
    return PALETTE[i % len(PALETTE)]


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
    header = f"objective = {evaluation.objective:g} | total fee = {evaluation.total_fee:g} | {status}"
    fig.suptitle(f"{title}\n{header}" if title else header)
    return fig


def _draw_deck(ax, state: State, s: int, used_weight: float) -> None:
    problem = state.problem
    ship = problem.ships[s]
    ax.set_label(f"deck:{ship.id}")
    ax.add_patch(Rectangle((0, 0), ship.width, ship.length, facecolor="#f4f4f4", edgecolor="black", linewidth=1.5))
    for x in range(1, ship.width):
        ax.plot([x, x], [0, ship.length], color="#d0d0d0", linewidth=0.5, zorder=0.5)
    for y in range(1, ship.length):
        ax.plot([0, ship.width], [y, y], color="#d0d0d0", linewidth=0.5, zorder=0.5)

    loaded = 0
    for i, (vehicle, placement) in enumerate(zip(problem.vehicles, state.positions)):
        if placement is None or placement[0] != s:
            continue
        loaded += 1
        _, x, y, orientation = placement
        cols, rows = dimensions(vehicle, orientation)
        inside = 0 <= x and 0 <= y and x + cols <= ship.width and y + rows <= ship.length
        ax.add_patch(Rectangle(
            (x, y), cols, rows, facecolor=vehicle_color(i), alpha=0.85 if inside else 0.45,
            edgecolor="black" if inside else VIOLATION_COLOR, linewidth=1 if inside else 1.5,
            linestyle="-" if inside else "--", zorder=2,
        ))
        ax.text(x + cols / 2, y + rows / 2, f"{vehicle.id}\n{orientation}", ha="center", va="center",
                fontsize=6 if min(cols, rows) == 1 else 7, zorder=4)

    # sel yang ditempati lebih dari satu kendaraan (grid berisi "A+B")
    for y, row in enumerate(state.deck_grids()[s]):
        for x, cell in enumerate(row):
            if "+" in cell:
                ax.add_patch(Rectangle((x, y), 1, 1, facecolor="none", edgecolor=VIOLATION_COLOR,
                                       hatch="xxx", linewidth=0, zorder=3))

    over = " (MELEBIHI)" if used_weight > ship.max_capacity + 1e-9 else ""
    ax.set_title(f"{ship.id} ({ship.width}x{ship.length})\n{loaded} kendaraan | berat "
                 f"{used_weight:g}/{ship.max_capacity:g}{over}", fontsize=9)
    right, bottom = _extent(state, s)
    ax.set_xlim(-1, right + 1)
    # y ke bawah: anchor (x, y) = sel kiri-atas (DESIGN §3)
    ax.set_ylim(bottom + 1, -1)
    ax.set_aspect("equal")
    # nomor kolom/baris di tengah sel, sumbu x di atas supaya dekat dengan anchor y = 0
    ax.set_xticks([x + 0.5 for x in range(ship.width)], labels=range(ship.width))
    ax.set_yticks([y + 0.5 for y in range(ship.length)], labels=range(ship.length))
    ax.xaxis.tick_top()
    ax.tick_params(labelsize=6, length=0)
    for side in ax.spines.values():
        side.set_visible(False)


def _extent(state: State, s: int) -> tuple[int, int]:
    """Batas kanan dan bawah area gambar kapal `s`: geladak, diperluas bila ada kendaraan yang keluar batas."""
    ship = state.problem.ships[s]
    right, bottom = ship.width, ship.length
    for vehicle, placement in zip(state.problem.vehicles, state.positions):
        if placement is not None and placement[0] == s:
            _, x, y, orientation = placement
            cols, rows = dimensions(vehicle, orientation)
            right, bottom = max(right, x + cols), max(bottom, y + rows)
    return right, bottom


def _draw_outside(ax, problem: Problem, state: State) -> None:
    ax.set_label("outside")
    ax.axis("off")
    outside = [(i, v) for i, (v, p) in enumerate(zip(problem.vehicles, state.positions)) if p is None]
    ax.set_title(f"Di luar kapal ({len(outside)})", fontsize=9)
    lines = [f"{v.id}  {v.width}x{v.length}  fee {v.shipping_fee:g}  berat {v.weight:g}" for _, v in outside]
    # dua kolom bila daftarnya panjang supaya tetap muat setinggi geladak
    per_column = max(1, -(-len(lines) // 2)) if len(lines) > 24 else max(1, len(lines))
    for k, (i, _) in enumerate(outside):
        col, row = divmod(k, per_column)
        ax.text(0.02 + 0.5 * col, 0.98 - row * 0.04, lines[k], transform=ax.transAxes, fontsize=6.5,
                va="top", family="monospace",
                bbox={"boxstyle": "square,pad=0.15", "facecolor": vehicle_color(i), "alpha": 0.5, "linewidth": 0})
    if not outside:
        ax.text(0.02, 0.98, "(tidak ada)", transform=ax.transAxes, fontsize=8, va="top")


def render_state_text(problem: Problem, state_data: dict[str, Any]) -> str:
    """State sebagai teks: value, grid tiap geladak (`.` kosong, `##` overlap), dan daftar kendaraan di luar."""
    state = State.from_dict(problem, state_data)
    evaluation = state.evaluate()
    width = max(len(v.id) for v in problem.vehicles)
    lines = [
        f"objective = {evaluation.objective:g} | total fee = {evaluation.total_fee:g} | "
        f"feasible = {evaluation.is_feasible} (overlap {evaluation.overlap_cells}, keluar batas "
        f"{evaluation.out_of_bound_cells}, kelebihan berat {evaluation.weight_units})"
    ]
    for s, (ship, grid) in enumerate(zip(problem.ships, state.deck_grids())):
        lines.append("")
        over = " (MELEBIHI)" if evaluation.used_weight[s] > ship.max_capacity + 1e-9 else ""
        lines.append(f"{ship.id} ({ship.width}x{ship.length}), berat {evaluation.used_weight[s]:g}/"
                     f"{ship.max_capacity:g}{over}")
        for row in grid:
            cells = ["#" * width if "+" in cell else (cell or ".") for cell in row]
            lines.append(" ".join(cell.ljust(width) for cell in cells).rstrip())

    outside = [v for v, p in zip(problem.vehicles, state.positions) if p is None]
    lines.append("")
    lines.append(f"Di luar kapal ({len(outside)}): " + (", ".join(v.id for v in outside) or "-"))
    return "\n".join(lines)


def save_run_states(problem: Problem, result: dict[str, Any], prefix: str | Path) -> list[Path]:
    """Simpan gambar state awal dan akhir dari dict hasil run ke `<prefix>_initial.png` dan `<prefix>_final.png`."""
    prefix = Path(prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    run = f"{result['algorithm']} | {result['instance']} | seed {result['seed']}"
    paths = []
    for key, label in (("initial_state", "initial"), ("final_state", "final")):
        path = prefix.with_name(f"{prefix.name}_{label}.png")
        draw_state(problem, result[key], title=f"{label.capitalize()} state | {run}").savefig(path, dpi=150)
        paths.append(path)
    return paths
