"""Objective function dengan penalty dan evaluasi penuh (full recompute).

Konsep state value: IF3070_Materi03-BeyondClassicalSearch, slide 12-13.

    f(s) = total_fee - P * (overlap_cells + out_of_bound_cells + weight_units)

    overlap_cells      = sum per sel geladak dari max(0, jumlah kendaraan di sel - 1)
    out_of_bound_cells = jumlah sel kendaraan yang berada di luar geladak
    weight_units       = sum per kapal dari ceil(kelebihan_berat / berat_minimum)
    P                  = max shipping_fee + 1

Karena P > fee kendaraan mana pun, mengeluarkan satu kendaraan yang melanggar selalu menaikkan f.
Untuk berat bilangan bulat (berat minimum >= 1), `weight_units` sama dengan kelebihan berat biasa.

`evaluate()` menghitung semuanya dari nol. Fungsi ini menjadi acuan kebenaran untuk delta evaluation
di `core/state.py` (lihat tests/test_state.py) dan dipakai untuk laporan hasil akhir.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from core.problem import Problem, Vehicle

H, V = "H", "V"
ORIENTATIONS = (H, V)

Placement = tuple[int, int, int, str] | None

EPS = 1e-9


def dimensions(vehicle: Vehicle, orientation: str) -> tuple[int, int]:
    """Ukuran (kolom, baris) yang ditempati kendaraan. H = width x length, V = diputar 90 derajat."""
    if orientation == H:
        return vehicle.width, vehicle.length
    return vehicle.length, vehicle.width


def footprint(vehicle: Vehicle, x: int, y: int, orientation: str) -> list[tuple[int, int]]:
    """Seluruh sel (x, y) yang ditempati kendaraan, termasuk sel yang mungkin di luar geladak."""
    cols, rows = dimensions(vehicle, orientation)
    return [(cx, cy) for cy in range(y, y + rows) for cx in range(x, x + cols)]


def penalty_coefficient(problem: Problem) -> float:
    """P = max fee + 1, sehingga satu unit pelanggaran selalu lebih mahal dari fee kendaraan mana pun."""
    return max(v.shipping_fee for v in problem.vehicles) + 1


def min_weight(problem: Problem) -> float:
    return min(v.weight for v in problem.vehicles)


def weight_units(used: float, capacity: float, unit: float) -> int:
    """Kelebihan berat dalam satuan `unit` (berat kendaraan teringan), dibulatkan ke atas."""
    excess = used - capacity
    if excess <= EPS:
        return 0
    return max(1, math.ceil(excess / unit - EPS))


@dataclass(frozen=True, slots=True)
class Evaluation:
    objective: float
    total_fee: float
    overlap_cells: int
    out_of_bound_cells: int
    weight_units: int
    used_weight: tuple[float, ...]
    occupied_cells: tuple[int, ...]

    @property
    def is_feasible(self) -> bool:
        return self.overlap_cells == 0 and self.out_of_bound_cells == 0 and self.weight_units == 0


def evaluate(problem: Problem, positions: Sequence[Placement]) -> Evaluation:
    """Hitung objective dan seluruh pelanggaran dari nol untuk `positions` (satu entri per kendaraan)."""
    n_ships = len(problem.ships)
    cell_count: list[Counter] = [Counter() for _ in range(n_ships)]
    used_weight = [0.0] * n_ships
    total_fee = 0.0
    out_of_bounds = 0

    for vehicle, placement in zip(problem.vehicles, positions, strict=True):
        if placement is None:
            continue
        s, x, y, orientation = placement
        ship = problem.ships[s]
        total_fee += vehicle.shipping_fee
        used_weight[s] += vehicle.weight
        for cx, cy in footprint(vehicle, x, y, orientation):
            if 0 <= cx < ship.width and 0 <= cy < ship.length:
                cell_count[s][cx, cy] += 1
            else:
                out_of_bounds += 1

    overlap = sum(c - 1 for counts in cell_count for c in counts.values() if c > 1)
    unit = min_weight(problem)
    units = sum(weight_units(used_weight[s], problem.ships[s].max_capacity, unit) for s in range(n_ships))
    objective = total_fee - penalty_coefficient(problem) * (overlap + out_of_bounds + units)
    return Evaluation(
        objective=objective,
        total_fee=total_fee,
        overlap_cells=overlap,
        out_of_bound_cells=out_of_bounds,
        weight_units=units,
        used_weight=tuple(used_weight),
        occupied_cells=tuple(len(counts) for counts in cell_count),
    )
