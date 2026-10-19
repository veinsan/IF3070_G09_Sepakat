"""State persoalan beserta delta evaluation (DESIGN §3–§4).

State menyimpan satu `Placement` per kendaraan (index sama dengan `problem.vehicles`) dan agregat yang
diperbarui secara incremental setiap kali satu kendaraan dipindah:

- `occupancy[ship][y * width + x]` = jumlah kendaraan di sel tersebut,
- jumlah sel overlap, jumlah sel di luar geladak, total fee, dan berat terpakai per kapal.

Memindah satu kendaraan hanya menyentuh sel lama dan sel baru kendaraan itu (O(luas kendaraan)), bukan
seluruh grid. Objective dihitung dari agregat dalam O(jumlah kapal). Hasilnya selalu sama dengan
`core.objective.evaluate()` (diuji di tests/test_state.py).

Semua algoritma search hanya memakai API kelas ini: `set`, `apply`, `delta`, `objective`, `copy`.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from core.objective import (
    ORIENTATIONS,
    Evaluation,
    Placement,
    dimensions,
    evaluate,
    footprint,
    min_weight,
    penalty_coefficient,
    weight_units,
)
from core.problem import Problem

# satu perubahan state: kendaraan ke-i dipindah ke placement baru (None = keluar kapal)
Change = tuple[int, Placement]


class State:
    __slots__ = ("problem", "_positions", "_occupancy", "_overlap", "_out_of_bounds", "_fee", "_weight",
                 "_penalty", "_unit")

    def __init__(self, problem: Problem, positions: Sequence[Placement] | None = None) -> None:
        """State baru. Tanpa `positions`, semua kendaraan berada di luar kapal."""
        self.problem = problem
        self._positions: list[Placement] = [None] * len(problem.vehicles)
        self._occupancy = [[0] * ship.area for ship in problem.ships]
        self._overlap = 0
        self._out_of_bounds = 0
        self._fee = 0.0
        self._weight = [0.0] * len(problem.ships)
        self._penalty = penalty_coefficient(problem)
        self._unit = min_weight(problem)
        if positions is not None:
            if len(positions) != len(problem.vehicles):
                raise ValueError(f"positions berisi {len(positions)} entri, kendaraan ada {len(problem.vehicles)}")
            for i, placement in enumerate(positions):
                self.set(i, placement)

    # --- akses -----------------------------------------------------------------------------

    @property
    def positions(self) -> tuple[Placement, ...]:
        return tuple(self._positions)

    def placement(self, i: int) -> Placement:
        return self._positions[i]

    @property
    def objective(self) -> float:
        return self._fee - self._penalty * (self._overlap + self._out_of_bounds + self._weight_units())

    @property
    def total_fee(self) -> float:
        return self._fee

    @property
    def is_feasible(self) -> bool:
        return self._overlap == 0 and self._out_of_bounds == 0 and self._weight_units() == 0

    def evaluate(self) -> Evaluation:
        """Evaluasi penuh dari nol (lebih lambat). Dipakai untuk laporan hasil, bukan di dalam loop search."""
        return evaluate(self.problem, self._positions)

    # --- perubahan -------------------------------------------------------------------------

    def set(self, i: int, placement: Placement) -> None:
        """Pindahkan kendaraan ke-i ke `placement` dan perbarui agregat secara incremental."""
        old = self._positions[i]
        if old is not None:
            self._update(i, old, -1)
        if placement is not None:
            self._update(i, placement, +1)
        self._positions[i] = placement

    def apply(self, changes: Sequence[Change]) -> list[Change]:
        """Terapkan beberapa perubahan berurutan. Mengembalikan daftar perubahan untuk membatalkannya."""
        undo = []
        for i, placement in changes:
            undo.append((i, self._positions[i]))
            self.set(i, placement)
        undo.reverse()
        return undo

    def delta(self, changes: Sequence[Change]) -> float:
        """Selisih objective jika `changes` diterapkan. State tidak berubah setelah pemanggilan."""
        # ponytail: apply lalu revert, biaya 2x luas kendaraan per perubahan. Kalau Steepest Ascent terlalu
        # lambat, hitung skor kandidat posisi langsung dari occupancy tanpa mutasi.
        before = self.objective
        undo = self.apply(changes)
        after = self.objective
        self.apply(undo)
        return after - before

    def copy(self) -> State:
        clone = State.__new__(State)
        clone.problem = self.problem
        clone._positions = list(self._positions)
        clone._occupancy = [list(cells) for cells in self._occupancy]
        clone._overlap = self._overlap
        clone._out_of_bounds = self._out_of_bounds
        clone._fee = self._fee
        clone._weight = list(self._weight)
        clone._penalty = self._penalty
        clone._unit = self._unit
        return clone

    # --- serialisasi (format output JSON, EXPERIMENTS §2) ----------------------------------

    def to_dict(self) -> dict:
        """Pemetaan semua kendaraan (di dalam dan di luar) + pemetaan sel tiap geladak (`decks`).

        `decks` hanya turunan dari `vehicles` untuk dibaca manusia/visualisasi, diabaikan oleh `from_dict`.
        """
        ships = self.problem.ships
        vehicles = []
        for vehicle, placement in zip(self.problem.vehicles, self._positions):
            if placement is None:
                vehicles.append({"id": vehicle.id, "ship": None})
            else:
                s, x, y, orientation = placement
                vehicles.append({"id": vehicle.id, "ship": ships[s].id, "x": x, "y": y, "orientation": orientation})
        decks = [{"id": ship.id, "grid": grid} for ship, grid in zip(ships, self.deck_grids())]
        return {"vehicles": vehicles, "decks": decks}

    def deck_grids(self) -> list[list[list[str]]]:
        """Per kapal, grid `[y][x]` berisi id kendaraan di sel itu: "" kosong, "A+B" bila overlap."""
        grids = [[[""] * ship.width for _ in range(ship.length)] for ship in self.problem.ships]
        for vehicle, placement in zip(self.problem.vehicles, self._positions):
            if placement is None:
                continue
            s, x, y, orientation = placement
            ship, grid = self.problem.ships[s], grids[s]
            for cx, cy in footprint(vehicle, x, y, orientation):
                if 0 <= cx < ship.width and 0 <= cy < ship.length:
                    grid[cy][cx] = f"{grid[cy][cx]}+{vehicle.id}" if grid[cy][cx] else vehicle.id
        return grids

    @classmethod
    def from_dict(cls, problem: Problem, data: dict) -> State:
        ship_index = {ship.id: s for s, ship in enumerate(problem.ships)}
        by_id = {entry["id"]: entry for entry in data["vehicles"]}
        positions: list[Placement] = []
        for vehicle in problem.vehicles:
            entry = by_id[vehicle.id]
            if entry["ship"] is None:
                positions.append(None)
            else:
                positions.append((ship_index[entry["ship"]], entry["x"], entry["y"], entry["orientation"]))
        return cls(problem, positions)

    def __repr__(self) -> str:
        loaded = sum(p is not None for p in self._positions)
        return f"State(objective={self.objective:g}, loaded={loaded}/{len(self._positions)})"

    # --- internal --------------------------------------------------------------------------

    def _weight_units(self) -> int:
        ships = self.problem.ships
        return sum(weight_units(self._weight[s], ships[s].max_capacity, self._unit) for s in range(len(ships)))

    def _update(self, i: int, placement: tuple[int, int, int, str], sign: int) -> None:
        """Tambah (sign=+1) atau keluarkan (sign=-1) kendaraan ke-i pada `placement` dari agregat."""
        s, x, y, orientation = placement
        vehicle = self.problem.vehicles[i]
        ship = self.problem.ships[s]
        occupancy = self._occupancy[s]
        cols, rows = dimensions(vehicle, orientation)
        for cy in range(y, y + rows):
            row_inside = 0 <= cy < ship.length
            for cx in range(x, x + cols):
                if not (row_inside and 0 <= cx < ship.width):
                    self._out_of_bounds += sign
                    continue
                k = cy * ship.width + cx
                if sign > 0:
                    if occupancy[k] > 0:
                        self._overlap += 1
                    occupancy[k] += 1
                else:
                    occupancy[k] -= 1
                    if occupancy[k] > 0:
                        self._overlap -= 1
        self._fee += sign * vehicle.shipping_fee
        self._weight[s] += sign * vehicle.weight


def random_placement(problem: Problem, rng: random.Random) -> tuple[int, int, int, str]:
    """Kapal, anchor, dan orientasi acak. Anchor selalu di dalam geladak, badan kendaraan bisa keluar."""
    s = rng.randrange(len(problem.ships))
    ship = problem.ships[s]
    return s, rng.randrange(ship.width), rng.randrange(ship.length), rng.choice(ORIENTATIONS)


def random_state(problem: Problem, rng: random.Random, p_inside: float = 0.5) -> State:
    """Initial state acak: tiap kendaraan masuk ke posisi acak dengan peluang `p_inside`, sisanya di luar."""
    return State(problem, [random_placement(problem, rng) if rng.random() < p_inside else None
                           for _ in problem.vehicles])
