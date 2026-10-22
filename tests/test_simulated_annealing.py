"""Test Simulated Annealing: T0 otomatis, laju pendinginan, dan loop utama."""

import json
import math
import random
import unittest

from dataclasses import replace

from config import DATA_DIR
from core.problem import load_problem, parse_problem
from core.state import State, random_state
from search.neighbors import random_neighbor
from search.simulated_annealing import cooling_rate, initial_temperature, simulated_annealing

DATA = DATA_DIR
MAIN = load_problem(DATA / "main.json")
SMALL = load_problem(DATA / "small.json")
MULTI = load_problem(DATA / "multi.json")

# parameter kecil supaya test cepat; nilai eksperimen ada di config.py
PARAMS = {"iterations": 5000, "t_min": 0.01, "t0_samples": 100, "t0_accept": 0.8, "stuck_window": 200}


def run(problem=SMALL, seed=1, **overrides):
    return simulated_annealing(problem, seed, **{**PARAMS, **overrides})


# deck 1x1 dan satu kendaraan 1x1: dari state kosong, satu-satunya move adalah memasukkan kendaraan (ΔE > 0)
TINY = parse_problem({
    "ships": [{"id": "D", "width": 1, "length": 1, "max_capacity": 5}],
    "vehicles": [{"id": "A", "width": 1, "length": 1, "shipping_fee": 3, "weight": 1, "eta": 1}],
})


class TestInitialTemperature(unittest.TestCase):
    def test_mean_worse_move_accepted_with_target_probability(self):
        state = random_state(MAIN, random.Random(1))
        t0 = initial_temperature(state, random.Random(7), samples=100, accept_prob=0.8)

        # ulangi sampling yang sama untuk mendapatkan ΔE move yang memperburuk
        rng = random.Random(7)
        worse = [d for d in (state.delta(random_neighbor(state, rng)) for _ in range(100)) if d < 0]
        self.assertGreater(t0, 0)
        self.assertAlmostEqual(math.exp((sum(worse) / len(worse)) / t0), 0.8)

    def test_state_unchanged_and_deterministic(self):
        state = random_state(MAIN, random.Random(2))
        positions, objective = state.positions, state.objective
        a = initial_temperature(state, random.Random(3), samples=50, accept_prob=0.8)
        b = initial_temperature(state, random.Random(3), samples=50, accept_prob=0.8)
        self.assertEqual(a, b)
        self.assertEqual(state.positions, positions)
        self.assertEqual(state.objective, objective)

    def test_no_worse_move_falls_back_to_one(self):
        state = State(TINY)
        self.assertEqual(initial_temperature(state, random.Random(0), samples=20, accept_prob=0.8), 1.0)

    def test_invalid_accept_prob(self):
        state = State(TINY)
        for p in (0, 1, 1.5):
            with self.assertRaises(ValueError):
                initial_temperature(state, random.Random(0), samples=10, accept_prob=p)


class TestCoolingRate(unittest.TestCase):
    def test_reaches_t_min_after_n_iterations(self):
        for t0, t_min, n in ((10_000, 0.01, 100_000), (5.0, 1.0, 10), (123.4, 0.5, 1)):
            alpha = cooling_rate(t0, t_min, n)
            self.assertLess(alpha, 1)
            self.assertAlmostEqual(t0 * alpha**n / t_min, 1.0)

    def test_no_heating_when_t0_below_t_min(self):
        self.assertEqual(cooling_rate(0.5, 1.0, 100), 1.0)

    def test_invalid_arguments(self):
        for args in ((10, 0.01, 0), (10, 0, 100), (10, -1, 100)):
            with self.assertRaises(ValueError):
                cooling_rate(*args)


class TestSimulatedAnnealing(unittest.TestCase):
    def test_same_seed_same_result(self):
        a, b = run(seed=4), run(seed=4)
        self.assertEqual(a.final_state.positions, b.final_state.positions)
        self.assertEqual(a.history, b.history)
        self.assertNotEqual(run(seed=5).history, a.history)

    def test_runs_exactly_n_iterations_and_ends_at_t_min(self):
        for seed in (1, 2, 3):
            result = run(seed=seed, iterations=1234, t_min=0.5)
            self.assertEqual(result.iterations, 1234)
            self.assertEqual(len(result.history["objective"]), 1235)
            self.assertAlmostEqual(result.extra["final_temperature"] / 0.5, 1.0)
            self.assertAlmostEqual(result.extra["alpha"], cooling_rate(result.extra["t0"], 0.5, 1234))

    def test_history_and_counters(self):
        result = run()
        history = result.history["objective"]
        self.assertEqual(history[0], result.initial_state.objective)
        self.assertEqual(result.evaluations, result.history["evaluations"][-1])
        self.assertGreaterEqual(result.evaluations, 1 + PARAMS["t0_samples"] + result.iterations)
        self.assertLessEqual(result.extra["accepted_worse"], result.iterations)

    def test_final_state_is_best_found(self):
        result = run()
        self.assertEqual(result.final_state.objective, result.history["best_feasible"][-1])
        self.assertEqual(result.extra["raw_best_objective"], max(result.history["objective"]))
        self.assertEqual(result.final_state.objective, result.final_state.evaluate().objective)

    def test_given_initial_state_is_used_and_not_modified(self):
        initial = random_state(SMALL, random.Random(9))
        positions = initial.positions
        result = run(initial=initial)
        self.assertEqual(result.initial_state.positions, positions)
        self.assertEqual(initial.positions, positions)
        self.assertEqual(result.history["objective"][0], initial.objective)

    def test_probability_history_only_for_worse_moves(self):
        result = run()
        objective, prob = result.history["objective"], result.history["prob"]
        iterations = [k for k, _ in prob]
        self.assertEqual(iterations, sorted(set(iterations)))
        self.assertTrue(all(1 <= k <= result.iterations for k in iterations))
        self.assertTrue(all(0 <= p <= 1 for _, p in prob))
        # di iterasi tanpa catatan prob (ΔE >= 0), objective tidak pernah turun
        recorded = set(iterations)
        for k in range(1, len(objective)):
            if k not in recorded:
                self.assertGreaterEqual(objective[k], objective[k - 1])
        # setiap langkah buruk yang diterima tercatat di prob dan membuat objective turun
        self.assertEqual(
            sum(objective[k] < objective[k - 1] for k in iterations), result.extra["accepted_worse"]
        )

    def test_subnanounit_improvement_is_not_a_local_optimum(self):
        tiny = replace(TINY, vehicles=(replace(TINY.vehicles[0], shipping_fee=5e-10),))
        loaded = State(tiny, [(0, 0, 0, "H")])
        result = run(problem=tiny, initial=loaded, seed=1, iterations=1, t0_samples=0, stuck_window=1)
        # Seed ini menerima removal; reinsertion masih memberi delta positif yang valid.
        self.assertEqual(result.history["objective"][-1], 0)
        self.assertEqual(result.extra["stuck_count"], 0)
        self.assertEqual(result.history["local_optimum"], [[1, False]])

    def test_confirmed_local_optimum_episode_counted_once(self):
        tiny = replace(TINY, vehicles=(replace(TINY.vehicles[0], shipping_fee=1000),))
        loaded = State(tiny, [(0, 0, 0, "H")])
        result = run(problem=tiny, initial=loaded, iterations=6, t0_samples=0, stuck_window=2)
        self.assertEqual(result.extra["stuck_count"], 1)
        self.assertEqual(result.extra["stuck_iterations"], [2])
        self.assertEqual(result.extra["stagnation_count"], 3)
        self.assertEqual(result.history["local_optimum"], [[2, True], [4, True], [6, True]])

    def test_nonfinite_temperature_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run(iterations=0, t_min=value)

    def test_no_stuck_when_window_exceeds_iterations(self):
        result = run(iterations=300, stuck_window=301)
        self.assertEqual(result.extra["stuck_count"], 0)

    def test_small_instance_reaches_feasible_solution(self):
        result = run(iterations=20_000)
        self.assertTrue(result.final_state.is_feasible)
        self.assertGreater(result.final_state.objective, result.initial_state.objective)

    def test_multi_ship_instance(self):
        result = run(problem=MULTI, iterations=20_000)
        self.assertTrue(result.final_state.is_feasible)
        ships_used = {p[0] for p in result.final_state.positions if p is not None}
        self.assertGreater(len(ships_used), 1)

    def test_result_is_json_serializable(self):
        data = json.loads(json.dumps(run(iterations=200).to_dict()))
        self.assertEqual(data["algorithm"], "sa")
        self.assertEqual(data["iterations"], 200)
        self.assertEqual(data["params"]["iterations"], 200)
        self.assertIn("alpha", data["extra"])


if __name__ == "__main__":
    unittest.main()
