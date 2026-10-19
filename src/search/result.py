"""Format hasil run yang seragam untuk semua algoritma (EXPERIMENTS §2).

Setiap algoritma (HC, SA, GA) mengembalikan `RunResult`. `to_dict()` menghasilkan dict siap-JSON yang
disimpan ke `output/` dan menjadi satu-satunya sumber untuk plot, visualisasi, dan tabel laporan, sehingga
semua itu bisa dibuat ulang tanpa menjalankan search lagi. `from_dict()` membaca kembali file tersebut.

Isi wajib menurut spesifikasi (bagian Cakupan) dan tempatnya di `RunResult`:

| Data                                         | Field                                         |
|----------------------------------------------|-----------------------------------------------|
| State awal dan akhir                         | `initial_state`, `final_state`                |
| Nilai objective akhir                        | `final_state.objective` (`final_objective`)   |
| Plot objective vs iterasi                    | `history["objective"]`                        |
| Durasi proses pencarian                      | `duration_s`                                  |
| Banyak iterasi (HC, SA, GA)                  | `iterations`                                  |
| `max_sideways`, `max_restart`, populasi, dll | `params`                                      |
| Banyak restart, iterasi per restart (RR HC)  | `extra["restarts"]`, `extra["iters_per_restart"]` |
| Plot e^(ΔE/T) vs iterasi (SA)                | `history["prob"]` = list `[iterasi, nilai]`   |
| Frekuensi stuck (SA)                         | `extra["stuck_count"]`                        |
| Plot max dan mean populasi (GA)              | `history["objective"]` (max), `history["mean"]` |
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.bounds import gap, upper_bound
from core.problem import Problem
from core.state import State


@dataclass
class RunResult:
    """Hasil satu run algoritma.

    `history["objective"][k]` = objective setelah iterasi ke-k (indeks 0 = state awal). Untuk GA, iterasi =
    generasi dan nilainya objective maksimum populasi. Key history lain bebas ditambah selama berupa list
    angka atau list pasangan `[iterasi, nilai]`.
    """

    algorithm: str
    seed: int | None
    params: dict[str, Any]
    initial_state: State
    final_state: State
    duration_s: float
    iterations: int
    # jumlah evaluasi objective: satu pemanggilan State.delta() atau satu state/individu baru yang dinilai
    evaluations: int
    history: dict[str, list] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if "objective" not in self.history:
            raise ValueError("history wajib berisi 'objective' (untuk plot objective vs iterasi)")
        if self.initial_state.problem is not self.final_state.problem:
            raise ValueError("initial_state dan final_state harus dari instance yang sama")

    @property
    def problem(self) -> Problem:
        return self.final_state.problem

    def to_dict(self) -> dict[str, Any]:
        final = self.final_state.evaluate()
        ships = self.problem.ships
        bound = upper_bound(self.problem)
        return {
            "algorithm": self.algorithm,
            "instance": self.problem.name,
            "seed": self.seed,
            "params": self.params,
            "initial_state": self.initial_state.to_dict(),
            "final_state": self.final_state.to_dict(),
            "initial_objective": self.initial_state.objective,
            "final_objective": final.objective,
            "total_fee": final.total_fee,
            "is_feasible": final.is_feasible,
            "violations": {
                "overlap_cells": final.overlap_cells,
                "out_of_bound_cells": final.out_of_bound_cells,
                "weight_units": final.weight_units,
            },
            "used_weight": list(final.used_weight),
            "capacity": [ship.max_capacity for ship in ships],
            "used_area_pct": 100 * sum(final.occupied_cells) / sum(ship.area for ship in ships),
            "loaded": sum(p is not None for p in self.final_state.positions),
            "upper_bound": bound,
            "gap_ub": gap(final.objective, bound),
            "duration_s": self.duration_s,
            "iterations": self.iterations,
            "evaluations": self.evaluations,
            "history": self.history,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, problem: Problem, data: dict[str, Any]) -> RunResult:
        """Baca kembali hasil `to_dict()`. Field turunan (objective, gap, dll.) dihitung ulang dari state."""
        if data["instance"] != problem.name:
            raise ValueError(f"hasil run untuk instance '{data['instance']}', bukan '{problem.name}'")
        return cls(
            algorithm=data["algorithm"],
            seed=data["seed"],
            params=data["params"],
            initial_state=State.from_dict(problem, data["initial_state"]),
            final_state=State.from_dict(problem, data["final_state"]),
            duration_s=data["duration_s"],
            iterations=data["iterations"],
            evaluations=data["evaluations"],
            history=data["history"],
            extra=data["extra"],
        )
