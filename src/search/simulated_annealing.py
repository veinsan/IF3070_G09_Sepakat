"""Simulated Annealing (DESIGN §6).

Sumber kuliah: M. L. Khodra, "Beyond Classical Search: Simulated Annealing", 2021,
https://www.youtube.com/watch?v=AdhG7HnhYrk (referensi [4] spesifikasi).

Move yang lebih baik selalu diterima. Move yang lebih buruk (ΔE < 0) diterima dengan peluang e^(ΔE/T),
dengan suhu T turun secara geometris setiap iterasi: T_k = T0 · α^k.

- T0 otomatis dari sampling random neighbor (`initial_temperature`).
- α dihitung dari T0 supaya suhu turun tepat dari T0 ke T_min dalam N iterasi (`cooling_rate`):
  T0 · α^N = T_min  =>  α = (T_min / T0)^(1/N). Dengan begitu semua run memiliki jumlah iterasi yang sama
  (N) walaupun T0 tiap seed berbeda, sehingga hasil antar-seed dan antar-algoritma lebih adil dibandingkan.

Parameter default ada di `config.py` (bagian Simulated Annealing), mengikuti pola `search/hill_climbing.py`.
"""

from __future__ import annotations

import math
import random
import time

from config import (
    INITIAL_P_INSIDE,
    SA_ITERATIONS,
    SA_STUCK_WINDOW,
    SA_T0_ACCEPT,
    SA_T0_SAMPLES,
    SA_T_MIN,
)
from core.problem import Problem
from core.state import State, initial_state
from search.neighbors import all_neighbors, random_neighbor
from search.result import FeasibleIncumbent, RunResult
from search.trace import SearchObserver


def initial_temperature(
    state: State, rng: random.Random, samples: int = SA_T0_SAMPLES, accept_prob: float = SA_T0_ACCEPT
) -> float:
    """T0 otomatis dari sampling `samples` random neighbor di sekitar `state`.

    Dari move yang memperburuk (ΔE < 0), T0 dipilih supaya move dengan ΔE rata-rata diterima dengan
    peluang `accept_prob`:

        e^(mean(ΔE) / T0) = accept_prob   =>   T0 = mean(ΔE) / ln(accept_prob)

    Kedua ruas pembagian negatif, jadi T0 positif. Bila tidak ada move yang memperburuk, T0 = 1.
    State tidak berubah. Setiap sampel dihitung sebagai satu evaluasi (`samples` evaluasi).
    """
    if not 0 < accept_prob < 1:
        raise ValueError(f"accept_prob harus di antara 0 dan 1, bukan {accept_prob}")
    if samples < 0:
        raise ValueError("samples harus >= 0")
    worse = []
    for _ in range(samples):
        d = state.delta(random_neighbor(state, rng))
        if d < 0:
            worse.append(d)
    if not worse:
        return 1.0
    return (sum(worse) / len(worse)) / math.log(accept_prob)


def cooling_rate(t0: float, t_min: float, iterations: int) -> float:
    """α sehingga T0 · α^iterations = t_min, yaitu α = (t_min / T0)^(1/iterations).

    Bila T0 <= t_min (suhu awal sudah sangat rendah), α = 1 sehingga suhu tetap dan tidak pernah naik.
    """
    if iterations < 1:
        raise ValueError(f"iterations harus >= 1, bukan {iterations}")
    if not math.isfinite(t_min) or t_min <= 0:
        raise ValueError(f"t_min harus finite dan > 0, bukan {t_min}")
    if not math.isfinite(t0) or t0 <= 0:
        raise ValueError(f"t0 harus finite dan > 0, bukan {t0}")
    if t0 <= t_min:
        return 1.0
    return (t_min / t0) ** (1 / iterations)


def simulated_annealing(
    problem: Problem,
    seed: int | None = None,
    initial: State | None = None,
    iterations: int = SA_ITERATIONS,
    t_min: float = SA_T_MIN,
    t0_samples: int = SA_T0_SAMPLES,
    t0_accept: float = SA_T0_ACCEPT,
    stuck_window: int = SA_STUCK_WINDOW,
    *,
    observer: SearchObserver | None = None,
) -> RunResult:
    """Simulated Annealing dari `initial` (default: state acak dari `seed`) selama tepat `iterations` iterasi.

    Setiap iterasi: ambil satu random neighbor, terima bila ΔE >= 0 atau dengan peluang e^(ΔE/T), lalu
    T = T · α. Suhu iterasi pertama = T0 dan setelah iterasi terakhir = `t_min` (`cooling_rate`).

    `final_state` adalah incumbent FEASIBLE terbaik yang dikunjungi, atau baseline kosong eksplisit
    bila pencarian belum mengunjungi state feasible. Tidak ada perbaikan tersembunyi setelah loop.
    `history["objective"]` mencatat objective state current di setiap iterasi (indeks 0 = state awal).
    `history["prob"]` berisi pasangan `[iterasi, e^(ΔE/T)]` hanya untuk iterasi dengan ΔE < 0, karena untuk
    ΔE >= 0 nilainya selalu 1 dan tidak informatif (DESIGN §6).

    Setiap `stuck_window` iterasi, neighborhood current diperiksa sampai ditemukan perbaikan atau habis.
    Satu episode stuck = rangkaian checkpoint tanpa neighbor membaik, dihitung hanya pada checkpoint
    pertama. Checkpoint dengan neighbor membaik mengakhiri episode. Ini observasi berkala, bukan deteksi
    setiap transisi. `stagnation_count` terpisah menghitung window tanpa raw-best baru.
    """
    if iterations < 0 or stuck_window < 1:
        raise ValueError("iterations harus >= 0 dan stuck_window harus >= 1")
    if not math.isfinite(t_min) or t_min <= 0:
        raise ValueError("t_min harus finite dan > 0")
    rng = random.Random(seed)
    initial = initial_state(problem, rng, initial, INITIAL_P_INSIDE)

    start = time.perf_counter()
    current = initial.copy()
    t0 = initial_temperature(current, rng, t0_samples, t0_accept)
    alpha = cooling_rate(t0, t_min, iterations) if iterations else 1.0
    evaluations = 1 + t0_samples
    best = current.objective
    history = [current.objective]
    incumbent = FeasibleIncumbent(problem)
    incumbent.observe(current)
    feasible_history = [incumbent.state.objective]
    evaluation_history = [evaluations]
    probabilities: list[list[float]] = []
    temperature = t0
    accepted_worse = 0
    since_best = 0  # iterasi berturut-turut tanpa objective terbaik baru
    stuck_iterations: list[int] = []
    stagnation_count = 0
    in_stuck_episode = False
    local_optimum_checks: list[list[int | bool]] = []
    confirmation_evaluations = 0
    if observer is not None:
        observer(0, current, incumbent.state, {"temperature": temperature})

    for k in range(1, iterations + 1):
        used_temperature = temperature
        changes = random_neighbor(current, rng)
        d = current.delta(changes)
        evaluations += 1
        improved = False
        if d >= 0:
            accept = True
        else:
            probability = math.exp(d / temperature)
            probabilities.append([k, probability])
            accept = rng.random() < probability
        if accept:
            current.apply(changes)
            if d < 0:
                accepted_worse += 1
            if current.objective > best:
                best = current.objective
                improved = True
        history.append(current.objective)
        incumbent.observe(current)
        feasible_history.append(incumbent.state.objective)
        temperature *= alpha

        since_best = 0 if improved else since_best + 1
        if since_best == stuck_window:
            stagnation_count += 1
            since_best = 0
        if k % stuck_window == 0:
            local_optimum = True
            for neighbor in all_neighbors(current):
                delta = current.delta(neighbor)
                evaluations += 1
                confirmation_evaluations += 1
                if delta > 0:
                    local_optimum = False
                    break
            local_optimum_checks.append([k, local_optimum])
            if local_optimum and not in_stuck_episode:
                stuck_iterations.append(k)
            in_stuck_episode = local_optimum
        evaluation_history.append(evaluations)
        if observer is not None:
            observer(k, current, incumbent.state,
                     {"temperature": used_temperature, "accepted": accept,
                      "delta": d, "probability": 1.0 if d >= 0 else probability})
    if observer is not None:
        observer(iterations, current, incumbent.state, {"event": "finished", "temperature": temperature})
    duration = time.perf_counter() - start

    return RunResult(
        algorithm="sa",
        seed=seed,
        params={
            "iterations": iterations,
            "t_min": t_min,
            "t0_samples": t0_samples,
            "t0_accept": t0_accept,
            "stuck_window": stuck_window,
            "initial_p_inside": INITIAL_P_INSIDE,
        },
        initial_state=initial,
        final_state=incumbent.state,
        duration_s=duration,
        iterations=iterations,
        evaluations=evaluations,
        history={"objective": history, "prob": probabilities, "best_feasible": feasible_history,
                 "evaluations": evaluation_history, "local_optimum": local_optimum_checks},
        extra={
            "t0": t0,
            "alpha": alpha,
            "final_temperature": temperature,
            "accepted_worse": accepted_worse,
            "final_current_objective": current.objective,
            "stuck_count": len(stuck_iterations),
            "stuck_iterations": stuck_iterations,
            "stagnation_count": stagnation_count,
            "confirmation_evaluations": confirmation_evaluations,
            **incumbent.metadata(current, best),
        },
    )
