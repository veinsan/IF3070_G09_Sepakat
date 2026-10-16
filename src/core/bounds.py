"""Acuan global optimum untuk analisis "seberapa dekat ke global optima" (DESIGN §6).

- `upper_bound()`: relaksasi 0/1 knapsack dua dimensi (total berat <= kapasitas, total luas <= luas
  geladak) yang mengabaikan geometri. Semua susunan feasible juga feasible di relaksasi ini, jadi
  UB >= global optimum sebenarnya dan `gap()` terhadap UB adalah batas atas gap sebenarnya.
- `brute_force()`: global optimum persis lewat backtracking + branch and bound. Eksponensial, hanya
  untuk instance kecil (`src/data/small.json`), sekaligus untuk mengukur seberapa longgar UB.
"""

from __future__ import annotations

import math

from core.objective import EPS, ORIENTATIONS, dimensions
from core.problem import Problem, Vehicle
from core.state import State


def fits_somewhere(problem: Problem, vehicle: Vehicle) -> bool:
    """Apakah kendaraan muat di salah satu geladak dalam salah satu orientasi."""
    for ship in problem.ships:
        for orientation in ORIENTATIONS:
            cols, rows = dimensions(vehicle, orientation)
            if cols <= ship.width and rows <= ship.length:
                return True
    return False


def upper_bound(problem: Problem) -> float:
    """Fee maksimum relaksasi knapsack (berat + luas, gabungan semua kapal) via dynamic programming.

    Berat dibulatkan ke bawah (`floor`) bersama kapasitas: untuk himpunan feasible, sum(floor(w)) <=
    sum(w) <= C sehingga sum(floor(w)) <= floor(C). Jadi relaksasi tetap valid untuk berat pecahan, dan
    persis sama untuk berat bulat. Kendaraan yang tidak muat di geladak mana pun dibuang.
    """
    area_cap = sum(ship.area for ship in problem.ships)
    weight_cap = math.floor(sum(ship.max_capacity for ship in problem.ships))

    # best[a][w] = fee maksimum dengan total luas <= a dan total berat (floor) <= w
    best = [[0.0] * (weight_cap + 1) for _ in range(area_cap + 1)]
    for vehicle in problem.vehicles:
        if not fits_somewhere(problem, vehicle):
            continue
        area, weight, fee = vehicle.area, math.floor(vehicle.weight), vehicle.shipping_fee
        for a in range(area_cap, area - 1, -1):
            row, prev = best[a], best[a - area]
            for w in range(weight_cap, weight - 1, -1):
                candidate = prev[w - weight] + fee
                if candidate > row[w]:
                    row[w] = candidate
    return best[area_cap][weight_cap]


def gap(value: float, bound: float) -> float:
    """(UB - f) / UB, yaitu batas atas jarak relatif solusi ke global optimum."""
    return (bound - value) / bound if bound else 0.0


def brute_force(problem: Problem, max_nodes: int = 5_000_000) -> State:
    """State feasible dengan fee maksimum (global optimum persis).

    Tiap kendaraan dicoba di luar kapal atau di setiap posisi yang masih feasible (di dalam geladak, tidak
    overlap, berat cukup). Sel yang terpakai disimpan sebagai bitmask. Cabang dipotong bila fee sekarang +
    fee seluruh kendaraan sisa tidak bisa melebihi solusi terbaik. Melempar `RuntimeError` bila node yang
    dikunjungi melebihi `max_nodes` (instance terlalu besar untuk brute force).
    """
    n = len(problem.vehicles)
    offsets = [0]
    for ship in problem.ships:
        offsets.append(offsets[-1] + ship.area)

    # placement unik per kendaraan: (bitmask sel, index kapal, placement). Orientasi kendaraan persegi
    # menghasilkan bitmask yang sama, jadi cukup dicoba sekali.
    options: list[list[tuple[int, int, tuple[int, int, int, str]]]] = []
    for vehicle in problem.vehicles:
        seen: dict[int, tuple[int, int, tuple[int, int, int, str]]] = {}
        for s, ship in enumerate(problem.ships):
            for orientation in ORIENTATIONS:
                cols, rows = dimensions(vehicle, orientation)
                for y in range(ship.length - rows + 1):
                    for x in range(ship.width - cols + 1):
                        mask = 0
                        for cy in range(y, y + rows):
                            for cx in range(x, x + cols):
                                mask |= 1 << (offsets[s] + cy * ship.width + cx)
                        seen.setdefault(mask, (mask, s, (s, x, y, orientation)))
        options.append(list(seen.values()))

    # kendaraan ber-fee besar dicoba dulu supaya solusi bagus cepat ditemukan dan pruning lebih efektif
    order = sorted(range(n), key=lambda i: -problem.vehicles[i].shipping_fee)
    remaining = [0.0] * (n + 1)
    for k in range(n - 1, -1, -1):
        remaining[k] = remaining[k + 1] + problem.vehicles[order[k]].shipping_fee

    capacity = [ship.max_capacity for ship in problem.ships]
    used_weight = [0.0] * len(problem.ships)
    positions: list = [None] * n
    best_fee = -1.0
    best_positions: list = list(positions)
    nodes = 0

    def search(k: int, used_cells: int, fee: float) -> None:
        nonlocal best_fee, best_positions, nodes
        nodes += 1
        if nodes > max_nodes:
            raise RuntimeError(f"brute force melebihi {max_nodes} node, instance terlalu besar")
        if fee + remaining[k] <= best_fee:
            return
        if k == n:
            best_fee, best_positions = fee, list(positions)
            return
        i = order[k]
        vehicle = problem.vehicles[i]
        for mask, s, placement in options[i]:
            if mask & used_cells or used_weight[s] + vehicle.weight > capacity[s] + EPS:
                continue
            used_weight[s] += vehicle.weight
            positions[i] = placement
            search(k + 1, used_cells | mask, fee + vehicle.shipping_fee)
            positions[i] = None
            used_weight[s] -= vehicle.weight
        search(k + 1, used_cells, fee)  # kendaraan i di luar kapal

    search(0, 0, 0.0)
    return State(problem, best_positions)
