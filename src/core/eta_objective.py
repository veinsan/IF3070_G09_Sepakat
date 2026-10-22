"""Objective alternatif berbasis urgensi ETA (Bonus 1, DESIGN §8).

Setiap kendaraan bernilai bobot urgensi, bukan shipping fee saja:

    w_i = fee_i · (1 + 1/(eta_i + 1))

Makin kecil ETA (makin mendesak), makin besar bobotnya: eta = 0 bernilai 2 · fee, eta besar mendekati fee.
`+ 1` di penyebut menjaga pembagian nol karena `eta` boleh 0 (DESIGN §2). Tidak ada variabel baru, hanya
`shipping_fee` dan `eta` yang sudah ada di input.

Objective ETA dipasang dengan mengganti `shipping_fee` tiap kendaraan menjadi w_i pada salinan instance
(`eta_problem`), sehingga `State`, delta evaluation, penalty, upper bound, dan format hasil tidak berubah:

- P = max w_i + 1 (`penalty_coefficient` pada instance turunan), sesuai syarat DESIGN §8, jadi properti
  "state infeasible selalu punya removal yang memperbaiki" (DESIGN §4) tetap berlaku.
- `upper_bound` dan `gap_ub` otomatis memakai bobot yang sama dengan objective yang dioptimasi.
- Semua algoritma (HC, SA, GA) bisa dipakai tanpa perubahan kode.

Konsekuensinya, `total_fee` di hasil run ETA adalah total bobot. Fee asli kendaraan yang dimuat disimpan
terpisah oleh `run_eta` di `extra["shipping_fee_total"]` untuk dibandingkan dengan run objective fee.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import replace
from typing import Any

from core.objective import Placement
from core.problem import Problem, Vehicle
from core.state import State

SUFFIX = "_eta"


def urgency_weight(vehicle: Vehicle) -> float:
    """w = fee · (1 + 1/(eta + 1))."""
    return vehicle.shipping_fee * (1 + 1 / (vehicle.eta + 1))


def eta_problem(problem: Problem) -> Problem:
    """Salinan `problem` dengan `shipping_fee` = bobot urgensi, nama `<nama>_eta`. `problem` tidak berubah.

    Urutan, id, ukuran, berat, dan ETA kendaraan tetap, jadi state dari instance asli dan turunannya saling
    kompatibel (`State.from_dict` hanya memakai id kendaraan dan kapal).
    """
    vehicles = tuple(replace(v, shipping_fee=urgency_weight(v)) for v in problem.vehicles)
    return replace(problem, vehicles=vehicles, name=problem.name + SUFFIX)


def shipping_fee_total(problem: Problem, positions: Sequence[Placement]) -> float:
    """Total fee asli kendaraan yang dimuat (`problem` = instance asli, bukan turunan ETA)."""
    return sum(v.shipping_fee for v, p in zip(problem.vehicles, positions, strict=True) if p is not None)


def run_eta(algorithm: Callable[..., Any], problem: Problem, seed: int | None = None, **params: Any):
    """Jalankan `algorithm(problem_eta, seed=seed, **params)` lalu catat objective dan fee asli di `extra`.

    `algorithm` = fungsi search mana pun yang mengembalikan `RunResult` (misalnya `simulated_annealing`).
    Dengan seed yang sama, initial state acaknya sama dengan run objective fee, karena pengacakan posisi
    tidak bergantung pada fee.
    """
    transformed = eta_problem(problem)
    initial = params.get("initial")
    if initial is not None:
        if initial.problem.ships != problem.ships or initial.problem.vehicles != problem.vehicles:
            raise ValueError("initial state ETA harus berasal dari problem asli yang sama")
        params["initial"] = State(transformed, initial.positions)
    result = algorithm(transformed, seed=seed, **params)
    result.extra["objective"] = "eta"
    result.extra["shipping_fee_total"] = shipping_fee_total(problem, result.final_state.positions)
    return result
