"""Test Steepest Ascent Hill-Climbing."""

import json
import random
import unittest

from config import DATA_DIR
from core.objective import EPS
from core.problem import load_problem, parse_problem
from core.state import State, random_state
from search.hill_climbing import best_neighbor, steepest_ascent
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
