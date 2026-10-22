"""Neighbor move sesuai spesifikasi; konsep neighbor dan successor: IF3070_Materi03-BeyondClassicalSearch, slide 15-18.

Satu `Move` adalah daftar `Change` yang bisa langsung diberikan ke `State.delta()` / `State.apply()`:

- `move(i, placement)`  : pindahkan kendaraan ke koordinat lain, ke luar kapal (None), atau dari luar ke dalam.
- `swap(i, j)`          : tukar anchor (kapal, x, y) dua kendaraan; tiap kendaraan mempertahankan
                          orientasinya. Kendaraan dari luar memakai orientasi pasangannya. Berlaku
                          dalam<->dalam dan dalam<->luar.
- `rotate(i)`           : ubah orientasi H<->V dengan anchor tetap, hanya untuk kendaraan di dalam.

`all_neighbors()` menghasilkan seluruh neighborhood (untuk Steepest Ascent), `random_neighbor()` satu
neighbor acak (untuk Stochastic HC, SA, dan mutasi GA).
"""

from __future__ import annotations

import random
from collections.abc import Iterator

from core.objective import ORIENTATIONS, H, V, Placement
from core.problem import Problem
from core.state import Change, State, random_placement

Move = list[Change]


def move(i: int, placement: Placement) -> Move:
    return [(i, placement)]


def swap(state: State, i: int, j: int) -> Move:
    pi, pj = state.placement(i), state.placement(j)
    return [(i, _take_anchor(pj, pi)), (j, _take_anchor(pi, pj))]


def rotate(state: State, i: int) -> Move:
    placement = state.placement(i)
    if placement is None:
        raise ValueError(f"kendaraan {i} di luar kapal, tidak bisa diputar")
    s, x, y, orientation = placement
    return [(i, (s, x, y, V if orientation == H else H))]


def can_rotate(problem: Problem, i: int) -> bool:
    """Kendaraan persegi diputar tetap menempati sel yang sama, jadi rotasinya tidak dihitung sebagai move."""
    vehicle = problem.vehicles[i]
    return vehicle.width != vehicle.length


def all_placements(problem: Problem) -> list[tuple[int, int, int, str]]:
    """Semua (kapal, x, y, orientasi) dengan anchor di dalam geladak."""
    return [
        (s, x, y, orientation)
        for s, ship in enumerate(problem.ships)
        for y in range(ship.length)
        for x in range(ship.width)
        for orientation in ORIENTATIONS
    ]


def all_neighbors(state: State) -> Iterator[Move]:
    """Seluruh neighbor dari state, tanpa duplikat dan tanpa move yang tidak mengubah apa pun.

    `move` melewati placement "anchor sama, orientasi lain" karena itu persis `rotate`.
    Ukuran: n x jumlah_placement - jumlah kendaraan di dalam (move) + pasangan yang tidak sama-sama di
    luar (swap) + kendaraan non-persegi di dalam (rotate).
    """
    problem = state.problem
    placements = all_placements(problem)
    n = len(problem.vehicles)

    for i in range(n):
        current = state.placement(i)
        for placement in placements:
            if current is None or placement[:3] != current[:3]:
                yield move(i, placement)
        if current is not None:
            yield move(i, None)

    for i in range(n):
        for j in range(i + 1, n):
            if state.placement(i) is None and state.placement(j) is None:
                continue
            changes = swap(state, i, j)
            if changes[0][1] != state.placement(i) or changes[1][1] != state.placement(j):
                yield changes

    for i in range(n):
        if state.placement(i) is not None and can_rotate(problem, i):
            yield rotate(state, i)


def random_neighbor(state: State, rng: random.Random) -> Move:
    """Satu neighbor acak: tipe move dipilih uniform (move/swap/rotate), lalu parameternya acak.

    Untuk `move` dari kendaraan di dalam, target "ke luar kapal" dan "ke koordinat acak" berpeluang sama.
    Kalau target dipilih uniform dari seluruh placement, peluang keluar hanya 1/(2·W·L + 1), sehingga
    kendaraan yang melanggar constraint hampir tidak pernah dikeluarkan.
    Bila tipe terpilih tidak mungkin (tidak ada kendaraan di dalam), dipakai `move`.
    """
    problem = state.problem
    inside = [i for i, p in enumerate(state.positions) if p is not None]
    kind = rng.choice(("move", "swap", "rotate"))

    if kind == "rotate":
        rotatable = [i for i in inside if can_rotate(problem, i)]
        if rotatable:
            return rotate(state, rng.choice(rotatable))
    elif kind == "swap" and inside and len(problem.vehicles) > 1:
        i = rng.choice(inside)
        j = rng.choice([k for k in range(len(problem.vehicles)) if k != i])
        return swap(state, i, j)

    i = rng.randrange(len(problem.vehicles))
    if state.placement(i) is not None and rng.random() < 0.5:
        return move(i, None)
    return move(i, random_placement(problem, rng))


def _take_anchor(source: Placement, own: Placement) -> Placement:
    """Anchor dari `source` dengan orientasi `own` (atau orientasi `source` bila `own` di luar kapal)."""
    if source is None:
        return None
    s, x, y, orientation = source
    return s, x, y, own[3] if own is not None else orientation
