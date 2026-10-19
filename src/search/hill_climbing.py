"""Hill-Climbing (DESIGN §7.1).

Steepest Ascent mengikuti salindia kuliah: di setiap iterasi seluruh neighbor dievaluasi, lalu pindah ke
neighbor terbaik hanya bila nilainya lebih besar dari state sekarang. Bila tidak ada neighbor yang lebih
baik, state sekarang adalah local optimum dan pencarian berhenti.

    current <- initial state
    loop:
        neighbor <- successor dengan value tertinggi
        if value(neighbor) <= value(current): return current
        current <- neighbor

Sumber: M. L. Khodra, "Beyond Classical Search: Hill-climbing Search", 2021,
https://www.youtube.com/watch?v=L0b0CN3Fds8 (referensi [3] spesifikasi).

Satu iterasi = satu langkah pindah ke neighbor yang lebih baik, sehingga `history["objective"]` berisi
`iterations + 1` nilai (indeks 0 = state awal). Evaluasi neighbor memakai delta evaluation (`State.delta`).
"""

from __future__ import annotations

import random
import time

from config import HC_MAX_ITERATIONS, INITIAL_P_INSIDE
from core.objective import EPS
from core.problem import Problem
from core.state import State, random_state
from search.neighbors import Move, all_neighbors
from search.result import RunResult


def best_neighbor(state: State, rng: random.Random) -> tuple[float, Move | None, int]:
    """Neighbor dengan delta objective terbesar beserta jumlah neighbor yang dievaluasi.

    Bila beberapa neighbor sama-sama terbaik, salah satunya dipilih acak dengan peluang sama (reservoir
    sampling), supaya hasil tidak bias ke urutan enumerasi (move selalu dienumerasi sebelum swap/rotate).
    """
    best_delta, best_move, ties, evaluated = float("-inf"), None, 0, 0
    for move in all_neighbors(state):
        delta = state.delta(move)
        evaluated += 1
        if delta > best_delta + EPS:
            best_delta, best_move, ties = delta, move, 1
        elif delta >= best_delta - EPS:
            ties += 1
            if rng.randrange(ties) == 0:
                best_move = move
    return best_delta, best_move, evaluated


def steepest_ascent(
    problem: Problem,
    seed: int | None = None,
    initial: State | None = None,
    max_iterations: int = HC_MAX_ITERATIONS,
) -> RunResult:
    """Steepest Ascent Hill-Climbing dari `initial` (default: state acak dari `seed`).

    `extra["stop_reason"]` = "local_optimum" (tidak ada neighbor yang lebih baik) atau "max_iterations".
    """
    rng = random.Random(seed)
    initial = initial.copy() if initial is not None else random_state(problem, rng, INITIAL_P_INSIDE)
    current = initial.copy()
    history = [current.objective]
    evaluations = 0
    stop_reason = "max_iterations"

    start = time.perf_counter()
    for _ in range(max_iterations):
        delta, move, evaluated = best_neighbor(current, rng)
        evaluations += evaluated
        if move is None or delta <= EPS:
            stop_reason = "local_optimum"
            break
        current.apply(move)
        history.append(current.objective)
    duration = time.perf_counter() - start

    return RunResult(
        algorithm="steepest",
        seed=seed,
        params={"max_iterations": max_iterations, "initial_p_inside": INITIAL_P_INSIDE},
        initial_state=initial,
        final_state=current,
        duration_s=duration,
        iterations=len(history) - 1,
        evaluations=evaluations,
        history={"objective": history},
        extra={"stop_reason": stop_reason},
    )
