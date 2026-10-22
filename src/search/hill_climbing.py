"""Hill-Climbing: Steepest Ascent, Sideways Move, Random Restart, dan Stochastic (DESIGN §7.1).

Semua varian mengikuti salindia kuliah. Sumber: M. L. Khodra, "Beyond Classical Search: Hill-climbing
Search", 2021, https://www.youtube.com/watch?v=L0b0CN3Fds8 (referensi [3] spesifikasi).

- Steepest Ascent : evaluasi seluruh neighbor, pindah ke yang terbaik bila lebih baik (Δ > 0).
                    Berhenti di local optimum.
- Sideways Move   : seperti Steepest, tapi boleh pindah ke neighbor terbaik yang sama nilainya (Δ = 0) untuk
                    keluar dari shoulder/plateau. Berhenti di local optimum ketat (semua Δ < 0) atau ketika
                    total sideways move yang sudah dilakukan mencapai `max_sideways`.
- Random Restart  : Steepest Ascent berulang dari initial state acak baru. Berhenti ketika banyak restart
                    mencapai `max_restart`; hasil = state terbaik dari semua percobaan.
- Stochastic      : ambil satu neighbor acak, pindah bila lebih baik. Berhenti setelah `max_no_improve`
                    neighbor berturut-turut tidak lebih baik, atau `max_iterations` tercapai.

Definisi iterasi (dicatat di `RunResult.iterations`, `history["objective"]` berisi `iterations + 1` nilai):
Steepest/Sideways = satu langkah pindah, Stochastic = satu neighbor acak yang dievaluasi, Random Restart =
total iterasi Steepest di semua percobaan + satu iterasi per restart (lompatan ke initial state baru).
Rincian per percobaan ada di `extra["iters_per_restart"]`.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

from config import (
    HC_MAX_ITERATIONS,
    HC_MAX_NO_IMPROVE,
    HC_MAX_RESTART,
    HC_MAX_SIDEWAYS,
    HC_STOCHASTIC_MAX_ITERATIONS,
    INITIAL_P_INSIDE,
)
from core.objective import EPS
from core.problem import Problem
from core.state import State, initial_state, random_state
from search.neighbors import Move, all_neighbors, random_neighbor
from search.result import FeasibleIncumbent, RunResult
from search.trace import SearchObserver


def best_neighbor(state: State, rng: random.Random) -> tuple[float, Move | None, int]:
    """Neighbor dengan delta objective terbesar beserta jumlah neighbor yang dievaluasi.

    Bila beberapa neighbor sama-sama terbaik, salah satunya dipilih acak dengan peluang sama (reservoir
    sampling), supaya hasil tidak bias ke urutan enumerasi (move selalu dienumerasi sebelum swap/rotate).
    Untuk Sideways Move ini juga berarti sideways move dipilih acak di antara neighbor yang setara.
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


@dataclass
class _Climb:
    """Jejak satu kali pendakian Steepest/Sideways pada `state` (state diubah in-place)."""

    state: State
    incumbent: FeasibleIncumbent
    feasible_history: list[float] = field(default_factory=list)
    evaluation_history: list[int] = field(default_factory=list)
    history: list[float] = field(default_factory=list)
    evaluations: int = 1
    sideways_moves: int = 0
    stop_reason: str = "max_iterations"

    @property
    def iterations(self) -> int:
        return len(self.history) - 1


def _climb(state: State, rng: random.Random, max_iterations: int, max_sideways: int,
           observer: SearchObserver | None = None, step_offset: int = 0,
           restart: int | None = None) -> _Climb:
    """Pendakian dengan neighbor terbaik. `max_sideways = 0` adalah Steepest Ascent murni."""
    if max_iterations < 0:
        raise ValueError("max_iterations harus >= 0")
    incumbent = FeasibleIncumbent(state.problem)
    incumbent.observe(state)
    climb = _Climb(state, incumbent, history=[state.objective],
                   feasible_history=[incumbent.state.objective], evaluation_history=[1])
    if observer is not None:
        details = {"restart": restart, "event": "restart"} if restart is not None else {}
        observer(step_offset, state, incumbent.state, details)
    for _ in range(max_iterations):
        delta, move, evaluated = best_neighbor(state, rng)
        climb.evaluations += evaluated
        if move is None or delta < -EPS or (delta <= EPS and climb.sideways_moves >= max_sideways):
            climb.stop_reason = "local_optimum"
            climb.evaluation_history[-1] = climb.evaluations
            break
        state.apply(move)
        incumbent.observe(state)
        climb.feasible_history.append(incumbent.state.objective)
        climb.evaluation_history.append(climb.evaluations)
        climb.history.append(state.objective)
        if observer is not None:
            details = {"restart": restart} if restart is not None else None
            observer(step_offset + climb.iterations, state, incumbent.state, details)
        if delta <= EPS:  # sideways move: nilai sama, state berbeda
            climb.sideways_moves += 1
            if climb.sideways_moves >= max_sideways:
                climb.stop_reason = "max_sideways"
                break
    if state.is_feasible and state.objective >= incumbent.state.objective:
        incumbent.state = state  # preserve the ordinary climb endpoint on a feasible plateau
    return climb


def _initial(problem: Problem, rng: random.Random, initial: State | None) -> State:
    return initial_state(problem, rng, initial, INITIAL_P_INSIDE)


def steepest_ascent(
    problem: Problem,
    seed: int | None = None,
    initial: State | None = None,
    max_iterations: int = HC_MAX_ITERATIONS,
    *,
    observer: SearchObserver | None = None,
) -> RunResult:
    """Steepest Ascent Hill-Climbing dari `initial` (default: state acak dari `seed`).

    `extra["stop_reason"]` = "local_optimum" (tidak ada neighbor yang lebih baik) atau "max_iterations".
    """
    rng = random.Random(seed)
    initial = _initial(problem, rng, initial)
    start = time.perf_counter()
    climb = _climb(initial.copy(), rng, max_iterations, max_sideways=0, observer=observer)
    if observer is not None:
        observer(climb.iterations, climb.state, climb.incumbent.state, {"event": "finished"})
    duration = time.perf_counter() - start
    return RunResult(
        algorithm="steepest",
        seed=seed,
        params={"max_iterations": max_iterations, "initial_p_inside": INITIAL_P_INSIDE},
        initial_state=initial,
        final_state=climb.incumbent.state,
        duration_s=duration,
        iterations=climb.iterations,
        evaluations=climb.evaluations,
        history={"objective": climb.history, "best_feasible": climb.feasible_history,
                 "evaluations": climb.evaluation_history},
        extra={"stop_reason": climb.stop_reason,
               **climb.incumbent.metadata(climb.state, max(climb.history))},
    )


def sideways_move(
    problem: Problem,
    seed: int | None = None,
    initial: State | None = None,
    max_sideways: int = HC_MAX_SIDEWAYS,
    max_iterations: int = HC_MAX_ITERATIONS,
    *,
    observer: SearchObserver | None = None,
) -> RunResult:
    """Hill-Climbing with Sideways Move.

    `max_sideways` dihitung **total** sepanjang run, sesuai spesifikasi: "ketika banyak sideways move yang
    dilakukan sudah mencapai maksimum, pencarian dihentikan". `extra["stop_reason"]` = "local_optimum"
    (semua neighbor lebih buruk), "max_sideways", atau "max_iterations".
    """
    if max_sideways < 1:
        raise ValueError("max_sideways harus >= 1 (max_sideways = 0 adalah Steepest Ascent)")
    rng = random.Random(seed)
    initial = _initial(problem, rng, initial)
    start = time.perf_counter()
    climb = _climb(initial.copy(), rng, max_iterations, max_sideways, observer=observer)
    if observer is not None:
        observer(climb.iterations, climb.state, climb.incumbent.state, {"event": "finished"})
    duration = time.perf_counter() - start
    return RunResult(
        algorithm="sideways",
        seed=seed,
        params={"max_sideways": max_sideways, "max_iterations": max_iterations, "initial_p_inside": INITIAL_P_INSIDE},
        initial_state=initial,
        final_state=climb.incumbent.state,
        duration_s=duration,
        iterations=climb.iterations,
        evaluations=climb.evaluations,
        history={"objective": climb.history, "best_feasible": climb.feasible_history,
                 "evaluations": climb.evaluation_history},
        extra={"stop_reason": climb.stop_reason, "sideways_moves": climb.sideways_moves,
               **climb.incumbent.metadata(climb.state, max(climb.history))},
    )


def random_restart(
    problem: Problem,
    seed: int | None = None,
    initial: State | None = None,
    max_restart: int = HC_MAX_RESTART,
    max_iterations: int = HC_MAX_ITERATIONS,
    *,
    observer: SearchObserver | None = None,
) -> RunResult:
    """Random-Restart Hill-Climbing: 1 percobaan awal + `max_restart` restart, masing-masing Steepest Ascent.

    Initial state percobaan pertama = `initial` (atau acak dari `seed`), restart memakai state acak baru dari
    RNG yang sama. `history["objective"]` = objective tiap iterasi semua percobaan disambung (pola gigi gergaji),
    `history["best"]` = objective terbaik sejauh ini pada iterasi yang sama.
    """
    if max_restart < 0:
        raise ValueError("max_restart harus >= 0")
    rng = random.Random(seed)
    initial = _initial(problem, rng, initial)

    start = time.perf_counter()
    observed_best = FeasibleIncumbent(problem) if observer is not None else None

    def observe_restart(step: int, current: State, best: State, details: dict | None = None) -> None:
        observed_best.observe(current)
        observer(step, current, observed_best.state, details)

    callback = observe_restart if observer is not None else None
    climbs = [_climb(initial.copy(), rng, max_iterations, max_sideways=0, observer=callback, restart=0)]
    offset = len(climbs[0].history)
    for restart in range(1, max_restart + 1):
        climb = _climb(random_state(problem, rng, INITIAL_P_INSIDE), rng, max_iterations,
                       max_sideways=0, observer=callback, step_offset=offset, restart=restart)
        climbs.append(climb)
        offset += len(climb.history)
    if observer is not None:
        final_best = max(climbs, key=lambda c: (c.incumbent.state.objective, c.incumbent.found))
        observer(offset - 1, climbs[-1].state, final_best.incumbent.state,
                 {"event": "finished", "restart": max_restart})
    duration = time.perf_counter() - start

    best_climb = max(climbs, key=lambda c: (c.incumbent.state.objective, c.incumbent.found))
    # disambung per percobaan: lompatan ke initial state acak berikutnya tercatat sebagai satu iterasi
    history = [value for climb in climbs for value in climb.history]
    best_so_far, best = [], float("-inf")
    for value in history:
        best = max(best, value)
        best_so_far.append(best)
    feasible_history, evaluation_history = [], []
    best_feasible, offset = 0.0, 0
    for climb in climbs:
        for value in climb.feasible_history:
            best_feasible = max(best_feasible, value)
            feasible_history.append(best_feasible)
        evaluation_history.extend(offset + count for count in climb.evaluation_history)
        offset += climb.evaluations

    return RunResult(
        algorithm="random_restart",
        seed=seed,
        params={"max_restart": max_restart, "max_iterations": max_iterations, "initial_p_inside": INITIAL_P_INSIDE},
        initial_state=initial,
        final_state=best_climb.incumbent.state,
        duration_s=duration,
        iterations=len(history) - 1,
        evaluations=sum(c.evaluations for c in climbs),
        history={"objective": history, "best": best_so_far, "best_feasible": feasible_history,
                 "evaluations": evaluation_history},
        extra={
            "restarts": len(climbs) - 1,
            "iters_per_restart": [c.iterations for c in climbs],
            "final_objective_per_restart": [c.state.objective for c in climbs],
            "best_restart": climbs.index(best_climb),
            "stop_reasons": [c.stop_reason for c in climbs],
            **best_climb.incumbent.metadata(climbs[-1].state, max(history)),
        },
    )


def stochastic(
    problem: Problem,
    seed: int | None = None,
    initial: State | None = None,
    max_no_improve: int = HC_MAX_NO_IMPROVE,
    max_iterations: int = HC_STOCHASTIC_MAX_ITERATIONS,
    *,
    observer: SearchObserver | None = None,
) -> RunResult:
    """Stochastic Hill-Climbing: satu neighbor acak per iterasi, diterima hanya bila lebih baik (Δ > 0).

    `extra["stop_reason"]` = "max_no_improve" atau "max_iterations".
    """
    if max_iterations < 0 or max_no_improve < 1:
        raise ValueError("max_iterations harus >= 0 dan max_no_improve harus >= 1")
    rng = random.Random(seed)
    initial = _initial(problem, rng, initial)
    current = initial.copy()
    history = [current.objective]
    incumbent = FeasibleIncumbent(problem)
    incumbent.observe(current)
    feasible_history = [incumbent.state.objective]
    evaluation_history = [1]
    no_improve = 0
    stop_reason = "max_iterations"

    start = time.perf_counter()
    if observer is not None:
        observer(0, current, incumbent.state, None)
    for _ in range(max_iterations):
        move = random_neighbor(current, rng)
        if current.delta(move) > EPS:
            current.apply(move)
            no_improve = 0
        else:
            no_improve += 1
        history.append(current.objective)
        incumbent.observe(current)
        feasible_history.append(incumbent.state.objective)
        evaluation_history.append(evaluation_history[-1] + 1)
        if observer is not None:
            observer(len(history) - 1, current, incumbent.state, None)
        if no_improve >= max_no_improve:
            stop_reason = "max_no_improve"
            break
    if observer is not None:
        observer(len(history) - 1, current, incumbent.state, {"event": "finished"})
    duration = time.perf_counter() - start

    return RunResult(
        algorithm="stochastic",
        seed=seed,
        params={"max_no_improve": max_no_improve, "max_iterations": max_iterations, "initial_p_inside": INITIAL_P_INSIDE},
        initial_state=initial,
        final_state=incumbent.state,
        duration_s=duration,
        iterations=len(history) - 1,
        evaluations=evaluation_history[-1],
        history={"objective": history, "best_feasible": feasible_history,
                 "evaluations": evaluation_history},
        extra={"stop_reason": stop_reason, "improvements": sum(b > a for a, b in zip(history, history[1:])),
               **incumbent.metadata(current, max(history))},
    )
