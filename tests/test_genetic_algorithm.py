"""Test Genetic Algorithm: roulette wheel, crossover, mutasi, elitism, dan loop utama."""

import json
import random
import unittest
from collections import Counter

from config import DATA_DIR
from core.objective import evaluate
from core.problem import load_problem
from core.state import random_state
from search.genetic_algorithm import crossover, genetic_algorithm, mutate, roulette_cumulative, spin
from search.result import RunResult

DATA = DATA_DIR
MAIN = load_problem(DATA / "main.json")
SMALL = load_problem(DATA / "small.json")
MULTI = load_problem(DATA / "multi.json")

# parameter kecil supaya test cepat; nilai eksperimen ada di config.py
PARAMS = {"population_size": 20, "iterations": 60, "p_crossover": 0.8, "p_mutation": 0.2, "elitism": 2}


def run(problem=SMALL, seed=1, **overrides):
    return genetic_algorithm(problem, seed, **{**PARAMS, **overrides})


class TestRoulette(unittest.TestCase):
    def test_windowing_makes_all_fitness_positive(self):
        cumulative = roulette_cumulative([-50, 10, -20], epsilon=1)
        # fit = f - min + ε = [1, 61, 31]
        self.assertEqual(cumulative, [1, 62, 93])

    def test_equal_objectives_give_uniform_wheel(self):
        self.assertEqual(roulette_cumulative([7, 7, 7, 7], epsilon=1), [1, 2, 3, 4])

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            roulette_cumulative([])
        with self.assertRaises(ValueError):
            roulette_cumulative([1, 2], epsilon=0)

    def test_spin_picks_first_index_reaching_r(self):
        class FixedRng:
            def __init__(self, r):
                self.r = r

            def uniform(self, a, b):
                return self.r

        cumulative = [1, 62, 93]
        self.assertEqual(spin(cumulative, FixedRng(0)), 0)
        self.assertEqual(spin(cumulative, FixedRng(1)), 0)
        self.assertEqual(spin(cumulative, FixedRng(1.5)), 1)
        self.assertEqual(spin(cumulative, FixedRng(62)), 1)
        self.assertEqual(spin(cumulative, FixedRng(93)), 2)

    def test_selection_frequency_proportional_to_fitness(self):
        objectives = [0, 10, 30, 60]
        cumulative = roulette_cumulative(objectives, epsilon=1)
        fitness = [f + 1 for f in objectives]
        rng = random.Random(5)
        spins = 40_000
        counts = Counter(spin(cumulative, rng) for _ in range(spins))
        for i, fit in enumerate(fitness):
            self.assertAlmostEqual(counts[i] / spins, fit / sum(fitness), delta=0.01)


class TestOperators(unittest.TestCase):
    def test_one_point_crossover_genes(self):
        rng = random.Random(1)
        a, b = random_state(MAIN, rng), random_state(MAIN, rng)
        a_pos, b_pos = a.positions, b.positions
        cut = 11
        c1, c2 = crossover(a, b, cut)
        self.assertEqual(c1.positions, a_pos[:cut] + b_pos[cut:])
        self.assertEqual(c2.positions, b_pos[:cut] + a_pos[cut:])
        # induk tidak berubah
        self.assertEqual((a.positions, b.positions), (a_pos, b_pos))

    def test_crossover_child_objective_matches_full_recompute(self):
        rng = random.Random(2)
        for problem in (MAIN, MULTI):
            for _ in range(30):
                a, b = random_state(problem, rng), random_state(problem, rng)
                for child in crossover(a, b, rng.randint(1, len(problem.vehicles) - 1)):
                    self.assertAlmostEqual(child.objective, evaluate(problem, child.positions).objective)

    def test_crossover_invalid_cut(self):
        rng = random.Random(3)
        a, b = random_state(SMALL, rng), random_state(SMALL, rng)
        for cut in (0, len(SMALL.vehicles)):
            with self.assertRaises(ValueError):
                crossover(a, b, cut)

    def test_mutation_changes_state_consistently(self):
        rng = random.Random(4)
        changed = 0
        for _ in range(50):
            state = random_state(MAIN, rng)
            before = state.positions
            mutate(state, rng)
            changed += state.positions != before
            self.assertAlmostEqual(state.objective, evaluate(MAIN, state.positions).objective)
        self.assertGreater(changed, 40)


class TestGeneticAlgorithm(unittest.TestCase):
    def test_history_lengths_and_counts(self):
        result = run(iterations=40, population_size=21)
        self.assertEqual(result.algorithm, "ga")
        self.assertEqual(result.iterations, 40)
        self.assertEqual(len(result.history["objective"]), 41)
        self.assertEqual(len(result.history["mean"]), 41)
        # populasi awal + anak baru tiap generasi (elit tidak dinilai ulang)
        self.assertEqual(result.evaluations, 21 + 40 * (21 - 2))
        self.assertEqual(result.history["evaluations"], [21 + k * 19 for k in range(41)])

    def test_max_never_below_mean(self):
        result = run()
        for best, mean in zip(result.history["objective"], result.history["mean"]):
            self.assertGreaterEqual(best + 1e-9, mean)

    def test_elitism_keeps_max_monotonic(self):
        maxima = run(problem=MAIN, elitism=1).history["objective"]
        self.assertTrue(all(b >= a for a, b in zip(maxima, maxima[1:])))

    def test_initial_and_final_state(self):
        result = run(problem=MAIN)
        self.assertEqual(result.initial_state.objective, result.history["objective"][0])
        self.assertEqual(result.final_state.objective, result.history["best_feasible"][-1])
        self.assertEqual(result.extra["raw_best_objective"], max(result.history["objective"]))
        self.assertAlmostEqual(result.final_state.objective,
                               evaluate(MAIN, result.final_state.positions).objective)

    def test_improves_on_initial_population(self):
        for problem in (MAIN, MULTI):
            result = run(problem=problem, iterations=150)
            self.assertGreater(result.final_state.objective, result.initial_state.objective)
            self.assertTrue(result.final_state.is_feasible)

    def test_zero_iterations(self):
        result = run(iterations=0)
        self.assertEqual(result.history["objective"], [result.initial_state.objective])
        self.assertEqual(result.evaluations, PARAMS["population_size"])

    def test_deterministic_for_same_seed(self):
        a, b = run(seed=7), run(seed=7)
        self.assertEqual(a.final_state.positions, b.final_state.positions)
        self.assertEqual(a.history, b.history)
        self.assertNotEqual(a.history, run(seed=8).history)

    def test_without_crossover_and_mutation_population_only_resamples(self):
        # tanpa variasi genetik, tidak mungkin muncul individu lebih baik dari populasi awal
        result = run(problem=MAIN, p_crossover=0, p_mutation=0)
        self.assertEqual(result.extra["crossovers"], 0)
        self.assertEqual(result.extra["mutations"], 0)
        self.assertEqual(result.final_state.objective, result.history["best_feasible"][0])

    def test_invalid_params(self):
        for overrides in ({"population_size": 1}, {"iterations": -1}, {"elitism": 20}, {"elitism": -1},
                          {"p_crossover": 1.5}, {"p_mutation": -0.1}):
            with self.subTest(**overrides), self.assertRaises(ValueError):
                run(**overrides)

    def test_nonfinite_epsilon_rejected_even_with_zero_generations(self):
        for epsilon in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(epsilon=epsilon), self.assertRaises(ValueError):
                run(iterations=0, epsilon=epsilon)

    def test_result_round_trip(self):
        result = run(problem=MAIN, iterations=20)
        data = json.loads(json.dumps(result.to_dict()))
        self.assertEqual(data["params"]["selection"], "roulette")
        self.assertEqual(data["params"]["population"], PARAMS["population_size"])
        loaded = RunResult.from_dict(MAIN, data)
        self.assertEqual(loaded.final_state.positions, result.final_state.positions)
        self.assertEqual(loaded.history, result.history)


if __name__ == "__main__":
    unittest.main()
