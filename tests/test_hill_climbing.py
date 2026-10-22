"""Test Hill-Climbing: Steepest Ascent, Sideways Move, Random Restart, Stochastic."""

import json
import random
import unittest

from config import DATA_DIR
from core.objective import EPS
from core.problem import load_problem, parse_problem
from core.state import State, random_state
from search.hill_climbing import best_neighbor, random_restart, sideways_move, steepest_ascent, stochastic
from search.neighbors import all_neighbors

SMALL = load_problem(DATA_DIR / "small.json")
SMALL_OPTIMUM = 287  # brute force, lihat tests/test_bounds.py


class TestSteepestAscent(unittest.TestCase):
    def test_stops_at_feasible_local_optimum(self):
        for seed in range(1, 6):
            with self.subTest(seed=seed):
                result = steepest_ascent(SMALL, seed=seed)
                final = result.final_state
                self.assertEqual(result.extra["stop_reason"], "local_optimum")
                self.assertTrue(final.is_feasible)  # properti penalty DESIGN §4
                self.assertTrue(all(final.delta(move) <= EPS for move in all_neighbors(final)))
                self.assertLessEqual(final.objective, SMALL_OPTIMUM)

    def test_history_strictly_increasing(self):
        result = steepest_ascent(SMALL, seed=1)
        history = result.history["objective"]
        self.assertEqual(len(history), result.iterations + 1)
        self.assertEqual(history[0], result.initial_state.objective)
        self.assertEqual(history[-1], result.final_state.objective)
        self.assertTrue(all(b > a for a, b in zip(history, history[1:])))
        self.assertGreater(result.evaluations, 0)
        json.dumps(result.to_dict())  # hasil harus bisa disimpan ke output/

    def test_seeded(self):
        a, b = steepest_ascent(SMALL, seed=7), steepest_ascent(SMALL, seed=7)
        self.assertEqual(a.final_state.positions, b.final_state.positions)
        self.assertEqual(a.history, b.history)

    def test_given_initial_not_mutated(self):
        initial = random_state(SMALL, random.Random(3))
        before = initial.positions
        result = steepest_ascent(SMALL, seed=3, initial=initial)
        self.assertEqual(initial.positions, before)
        self.assertEqual(result.initial_state.positions, before)

    def test_max_iterations(self):
        result = steepest_ascent(SMALL, seed=1, max_iterations=1)
        self.assertEqual(result.iterations, 1)
        self.assertEqual(result.extra["stop_reason"], "max_iterations")
        self.assertEqual(result.params["max_iterations"], 1)


class TestSidewaysMove(unittest.TestCase):
    def test_sideways_limit_is_total(self):
        for seed in range(1, 4):
            with self.subTest(seed=seed):
                result = sideways_move(SMALL, seed=seed, max_sideways=5)
                history = result.history["objective"]
                flat = sum(b == a for a, b in zip(history, history[1:]))
                self.assertEqual(result.extra["sideways_moves"], flat)  # sideways = langkah dengan Δ = 0
                self.assertLessEqual(flat, 5)
                self.assertTrue(all(b >= a for a, b in zip(history, history[1:])))
                if result.extra["stop_reason"] == "max_sideways":
                    self.assertEqual(flat, 5)
                else:
                    self.assertEqual(result.extra["stop_reason"], "local_optimum")
                    final = result.final_state
                    self.assertTrue(all(final.delta(move) < -EPS for move in all_neighbors(final)))
                self.assertTrue(result.final_state.is_feasible)
                self.assertEqual(result.params["max_sideways"], 5)

    def test_continues_past_steepest_local_optimum(self):
        steep, side = steepest_ascent(SMALL, seed=1), sideways_move(SMALL, seed=1, max_sideways=50)
        self.assertEqual(side.history["objective"][: steep.iterations + 1], steep.history["objective"])
        self.assertGreater(side.iterations, steep.iterations)
        self.assertGreaterEqual(side.final_state.objective, steep.final_state.objective)

    def test_rejects_zero_limit(self):
        with self.assertRaises(ValueError):
            sideways_move(SMALL, seed=1, max_sideways=0)


class TestRandomRestart(unittest.TestCase):
    def test_restart_bookkeeping(self):
        result = random_restart(SMALL, seed=2, max_restart=4)
        extra = result.extra
        self.assertEqual(extra["restarts"], 4)
        self.assertEqual(len(extra["iters_per_restart"]), 5)
        self.assertEqual(result.iterations, sum(extra["iters_per_restart"]) + extra["restarts"])
        self.assertEqual(len(result.history["objective"]), result.iterations + 1)
        self.assertEqual(result.final_state.objective, max(extra["final_objective_per_restart"]))
        self.assertEqual(result.history["best"][-1], result.final_state.objective)
        self.assertTrue(result.final_state.is_feasible)
        self.assertEqual(result.params["max_restart"], 4)

    def test_first_climb_is_steepest_ascent(self):
        steep, restart = steepest_ascent(SMALL, seed=3), random_restart(SMALL, seed=3, max_restart=3)
        self.assertEqual(restart.extra["iters_per_restart"][0], steep.iterations)
        self.assertGreaterEqual(restart.final_state.objective, steep.final_state.objective)
        self.assertEqual(restart.initial_state.positions, steep.initial_state.positions)

    def test_zero_restart_equals_steepest(self):
        steep, restart = steepest_ascent(SMALL, seed=4), random_restart(SMALL, seed=4, max_restart=0)
        self.assertEqual(restart.final_state.positions, steep.final_state.positions)
        self.assertEqual(restart.extra["restarts"], 0)


class TestStochastic(unittest.TestCase):
    def test_stops_after_no_improvement(self):
        result = stochastic(SMALL, seed=1, max_no_improve=500)
        history = result.history["objective"]
        self.assertEqual(result.extra["stop_reason"], "max_no_improve")
        self.assertEqual(len(history), result.iterations + 1)
        self.assertEqual(result.evaluations, result.iterations + 1)
        self.assertTrue(all(b >= a for a, b in zip(history, history[1:])))
        self.assertEqual(len(set(history[-501:])), 1)  # 500 iterasi terakhir tanpa perbaikan
        self.assertEqual(result.extra["improvements"], sum(b > a for a, b in zip(history, history[1:])))

    def test_max_iterations(self):
        result = stochastic(SMALL, seed=1, max_no_improve=10**9, max_iterations=300)
        self.assertEqual(result.iterations, 300)
        self.assertEqual(result.extra["stop_reason"], "max_iterations")

    def test_seeded(self):
        a, b = stochastic(SMALL, seed=5, max_no_improve=300), stochastic(SMALL, seed=5, max_no_improve=300)
        self.assertEqual(a.history, b.history)
        self.assertEqual(a.final_state.positions, b.final_state.positions)


class TestBestNeighbor(unittest.TestCase):
    def test_random_tie_breaking(self):
        # satu kendaraan 1x1 di deck kosong 2x2: memasukkannya ke sel mana pun sama baiknya
        problem = parse_problem({
            "ships": [{"id": "D", "width": 2, "length": 2, "max_capacity": 10}],
            "vehicles": [{"id": "A", "width": 1, "length": 1, "shipping_fee": 5, "weight": 1, "eta": 1}],
        })
        state = State(problem)
        chosen = set()
        for seed in range(40):
            delta, move, evaluated = best_neighbor(state, random.Random(seed))
            self.assertEqual(delta, 5)
            self.assertEqual(evaluated, 8)  # 4 anchor x 2 orientasi
            chosen.add(move[0][1][1:3])
        self.assertEqual(len(chosen), 4)  # keempat sel pernah terpilih


if __name__ == "__main__":
    unittest.main()
