"""Genetic Algorithm dengan roulette wheel selection (DESIGN §7.3).

Sumber kuliah: M. L. Khodra, "Beyond Classical Search: Genetic Algorithm", 2021,
https://www.youtube.com/watch?v=aI41TGo9J9c (referensi [5] spesifikasi).

- Chromosome = list `pos` milik `State` (satu gene per kendaraan, urutan index tetap), sehingga GA memakai
  objective dan delta evaluation yang sama dengan HC dan SA.
- Fitness roulette dari objective dengan windowing: fit_i = f_i − min_j f_j + ε. Objective bisa negatif karena
  penalty, padahal peluang roulette harus ≥ 0. ε > 0 membuat individu terburuk tetap punya peluang terpilih.
- Selection: roulette wheel eksplisit. Cumulative sum fitness dibuat sekali per generasi, lalu setiap spin
  mengambil r ~ U(0, Σfit) dan memilih individu pertama dengan cumsum ≥ r (`bisect`).
- Crossover: one-point pada index kendaraan dengan peluang `p_c`, menghasilkan dua anak.
- Mutation: dengan peluang `p_m`, terapkan satu random neighbor (move/swap/rotate, DESIGN §5) ke anak.
- Elitism: `elitism` individu terbaik dibawa langsung ke generasi berikutnya (heuristik tambahan).

Parameter default ada di `config.py` (bagian Genetic Algorithm). Sesuai spesifikasi, eksperimen hanya
memvariasikan `population_size` dan `iterations` (generasi); `p_c`, `p_m`, dan elitism tetap.
"""

from __future__ import annotations

import bisect
import itertools
import math
import random
import time
from collections.abc import Sequence

from config import (
    GA_ELITISM,
    GA_EPSILON,
    GA_ITERATIONS,
    GA_P_CROSSOVER,
    GA_P_MUTATION,
    GA_POPULATION,
    INITIAL_P_INSIDE,
)
from core.problem import Problem
from core.state import State, random_state
from search.neighbors import random_neighbor
from search.result import FeasibleIncumbent, RunResult


def roulette_cumulative(objectives: Sequence[float], epsilon: float = GA_EPSILON) -> list[float]:
    """Cumulative sum fitness roulette dengan windowing fit_i = f_i − min_j f_j + ε.

    Elemen terakhir = Σfit. Peluang individu ke-i terpilih = fit_i / Σfit.
    """
    if not objectives:
        raise ValueError("populasi kosong")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError(f"epsilon harus finite dan > 0, bukan {epsilon}")
    if not all(math.isfinite(value) for value in objectives):
        raise ValueError("objective roulette harus finite")
    worst = min(objectives)
    return list(itertools.accumulate(f - worst + epsilon for f in objectives))


def spin(cumulative: Sequence[float], rng: random.Random) -> int:
    """Satu putaran roda: r ~ U(0, Σfit), pilih index pertama dengan cumsum ≥ r."""
    r = rng.uniform(0, cumulative[-1])
    # bisect_left = index pertama dengan cumulative[i] >= r; min() menjaga r == Σfit akibat pembulatan float
    return min(bisect.bisect_left(cumulative, r), len(cumulative) - 1)


def crossover(a: State, b: State, cut: int) -> tuple[State, State]:
    """One-point crossover: anak 1 = a[:cut] + b[cut:], anak 2 = b[:cut] + a[cut:].

    Anak dibangun dari salinan induk lalu hanya gene yang berbeda di-`set`, jadi biayanya sebanding dengan
    banyak gene yang berubah (delta evaluation), bukan seluruh grid.
    """
    n = len(a.problem.vehicles)
    if not 0 < cut < n:
        raise ValueError(f"titik potong harus di antara 1 dan {n - 1}, bukan {cut}")
    child1, child2 = a.copy(), b.copy()
    for i in range(cut, n):
        pa, pb = a.placement(i), b.placement(i)
        if pa != pb:
            child1.set(i, pb)
            child2.set(i, pa)
    return child1, child2


def mutate(state: State, rng: random.Random) -> None:
    """Terapkan satu random neighbor (DESIGN §5) ke `state` secara in-place."""
    state.apply(random_neighbor(state, rng))


def genetic_algorithm(
    problem: Problem,
    seed: int | None = None,
    population_size: int = GA_POPULATION,
    iterations: int = GA_ITERATIONS,
    p_crossover: float = GA_P_CROSSOVER,
    p_mutation: float = GA_P_MUTATION,
    elitism: int = GA_ELITISM,
    epsilon: float = GA_EPSILON,
) -> RunResult:
    """GA selama tepat `iterations` generasi dengan populasi berukuran tetap `population_size`.

    Populasi awal = `population_size` state acak dari `seed` (`random_state`, sama dengan initial state HC/SA).
    Setiap generasi: `elitism` individu terbaik dibawa langsung, sisanya diisi pasangan anak dari dua induk
    hasil roulette (crossover dengan peluang `p_crossover`, lalu masing-masing anak dimutasi dengan peluang
    `p_mutation`).

    - `initial_state` = individu terbaik populasi awal, sehingga `history["objective"][0]` = objective-nya.
    - `final_state` = individu FEASIBLE terbaik yang dikunjungi pada generasi mana pun, atau baseline
      kosong eksplisit bila belum ada individu feasible. Populasi random dan seleksi tetap tidak diubah.
    - `history["objective"][k]` = objective maksimum populasi generasi ke-k (indeks 0 = populasi awal),
      `history["mean"][k]` = rata-rata objective populasi.
    - `evaluations` = banyak individu yang dinilai: populasi awal + semua anak baru (elit tidak dinilai ulang).
    """
    if population_size < 2:
        raise ValueError(f"population_size harus >= 2, bukan {population_size}")
    if iterations < 0:
        raise ValueError(f"iterations harus >= 0, bukan {iterations}")
    if not 0 <= elitism < population_size:
        raise ValueError(f"elitism harus di antara 0 dan {population_size - 1}, bukan {elitism}")
    for name, p in (("p_crossover", p_crossover), ("p_mutation", p_mutation)):
        if not 0 <= p <= 1:
            raise ValueError(f"{name} harus di antara 0 dan 1, bukan {p}")
    if not math.isfinite(epsilon) or epsilon <= 0:
        raise ValueError("epsilon harus finite dan > 0")
    n = len(problem.vehicles)

    rng = random.Random(seed)
    start = time.perf_counter()
    population = [random_state(problem, rng, INITIAL_P_INSIDE) for _ in range(population_size)]
    evaluations = population_size
    objectives = [s.objective for s in population]
    initial = population[_argmax(objectives)].copy()
    raw_best = initial.objective
    raw_best_generation = 0
    incumbent = FeasibleIncumbent(problem)
    for state in population:
        incumbent.observe(state)
    best_generation = 0 if incumbent.found else None
    history_max = [raw_best]
    feasible_history = [incumbent.state.objective]
    evaluation_history = [evaluations]
    history_mean = [sum(objectives) / population_size]
    crossovers = mutations = 0

    for generation in range(1, iterations + 1):
        ranked = sorted(range(population_size), key=objectives.__getitem__, reverse=True)
        offspring = [population[i] for i in ranked[:elitism]]
        offspring_objectives = [objectives[i] for i in ranked[:elitism]]
        cumulative = roulette_cumulative(objectives, epsilon)

        while len(offspring) < population_size:
            a, b = population[spin(cumulative, rng)], population[spin(cumulative, rng)]
            if n > 1 and rng.random() < p_crossover:
                children = crossover(a, b, rng.randint(1, n - 1))
                crossovers += 1
            else:
                children = a.copy(), b.copy()
            for child in children:
                if len(offspring) == population_size:
                    break
                if rng.random() < p_mutation:
                    mutate(child, rng)
                    mutations += 1
                offspring.append(child)
                offspring_objectives.append(child.objective)
                if incumbent.observe(child):
                    best_generation = generation
                evaluations += 1

        population = offspring
        objectives = offspring_objectives
        top = _argmax(objectives)
        if objectives[top] > raw_best:
            raw_best = objectives[top]
            raw_best_generation = generation
        history_max.append(objectives[top])
        history_mean.append(sum(objectives) / population_size)
        feasible_history.append(incumbent.state.objective)
        evaluation_history.append(evaluations)
    duration = time.perf_counter() - start

    return RunResult(
        algorithm="ga",
        seed=seed,
        params={
            "population": population_size,
            "iterations": iterations,
            "p_c": p_crossover,
            "p_m": p_mutation,
            "elitism": elitism,
            "epsilon": epsilon,
            "selection": "roulette",
            "initial_p_inside": INITIAL_P_INSIDE,
        },
        initial_state=initial,
        final_state=incumbent.state,
        duration_s=duration,
        iterations=iterations,
        evaluations=evaluations,
        history={"objective": history_max, "mean": history_mean,
                 "best_feasible": feasible_history, "evaluations": evaluation_history},
        extra={
            "best_generation": best_generation,
            "raw_best_generation": raw_best_generation,
            "crossovers": crossovers,
            "mutations": mutations,
            "final_mean": history_mean[-1],
            "final_feasible_count": sum(s.is_feasible for s in population),
            **incumbent.metadata(population[_argmax(objectives)], raw_best),
        },
    )


def _argmax(values: Sequence[float]) -> int:
    return max(range(len(values)), key=values.__getitem__)
