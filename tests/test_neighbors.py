"""Test neighbor move: semantik move/swap/rotate, ukuran neighborhood, dan random neighbor."""

import random
import unittest
from collections import Counter

from core.problem import parse_problem
from core.state import State, random_state
from search.neighbors import all_neighbors, all_placements, random_neighbor, rotate, swap

PROBLEM = parse_problem({
    "ships": [{"id": "D", "width": 3, "length": 4, "max_capacity": 10}],
    "vehicles": [
        {"id": "A", "width": 1, "length": 2, "shipping_fee": 5, "weight": 1, "eta": 1},
        {"id": "B", "width": 2, "length": 3, "shipping_fee": 9, "weight": 3, "eta": 1},
        {"id": "C", "width": 2, "length": 2, "shipping_fee": 7, "weight": 2, "eta": 1},
        {"id": "D", "width": 1, "length": 3, "shipping_fee": 4, "weight": 1, "eta": 1},
    ],
})


def normalized(positions):
    """Orientasi kendaraan persegi tidak berpengaruh pada sel yang ditempati, jadi disamakan ke H."""
    return tuple(
        p if p is None or v.width != v.length else (*p[:3], "H") for v, p in zip(PROBLEM.vehicles, positions)
    )


def result_of(state, changes):
    clone = state.copy()
    clone.apply(changes)
    return clone.positions


class TestMoves(unittest.TestCase):
    def test_swap_inside_inside_keeps_orientation(self):
        state = State(PROBLEM, [(0, 0, 0, "H"), (0, 1, 1, "V"), None, None])
        self.assertEqual(result_of(state, swap(state, 0, 1))[:2], ((0, 1, 1, "H"), (0, 0, 0, "V")))

    def test_swap_inside_outside(self):
        state = State(PROBLEM, [(0, 2, 1, "V"), None, None, None])
        positions = result_of(state, swap(state, 0, 1))
        self.assertIsNone(positions[0])
        self.assertEqual(positions[1], (0, 2, 1, "V"))

    def test_rotate(self):
        state = State(PROBLEM, [(0, 1, 2, "H"), None, None, None])
        self.assertEqual(rotate(state, 0), [(0, (0, 1, 2, "V"))])
        with self.assertRaises(ValueError):
            rotate(state, 1)


class TestAllNeighbors(unittest.TestCase):
    def test_size_and_no_noop(self):
        state = State(PROBLEM, [(0, 0, 0, "H"), (0, 1, 0, "V"), (0, 0, 2, "H"), None])
        neighbors = list(all_neighbors(state))
        kinds = Counter(len(changes) for changes in neighbors)

        n_placements = len(all_placements(PROBLEM))
        self.assertEqual(n_placements, 3 * 4 * 2)
        moves = 3 * (n_placements - 2 + 1) + n_placements
        swaps = 6
        rotates = 2
        self.assertEqual(kinds[1], moves + rotates)
        self.assertEqual(kinds[2], swaps)

        results = [result_of(state, changes) for changes in neighbors]
        self.assertNotIn(state.positions, results)
        self.assertEqual(len(results), len(set(results)), "neighbor duplikat")

    def test_skips_swap_of_two_outside(self):
        state = State(PROBLEM)
        self.assertTrue(all(len(changes) == 1 for changes in all_neighbors(state)))


class TestRandomNeighbor(unittest.TestCase):
    def test_subset_of_full_neighborhood(self):
        rng = random.Random(0)
        for _ in range(20):
            state = random_state(PROBLEM, rng)
            full = {normalized(result_of(state, changes)) for changes in all_neighbors(state)}
            full.add(normalized(state.positions))
            for _ in range(200):
                self.assertIn(normalized(result_of(state, random_neighbor(state, rng))), full)

    def test_all_kinds_and_removal_reachable(self):
        rng = random.Random(1)
        state = State(PROBLEM, [(0, 0, 0, "H"), (0, 1, 0, "V"), None, None])
        seen = Counter()
        for _ in range(3000):
            changes = random_neighbor(state, rng)
            if len(changes) == 2:
                seen["swap"] += 1
            elif changes[0][1] is None:
                seen["remove"] += 1
            elif state.placement(changes[0][0]) is not None and changes[0][1][:3] == state.placement(changes[0][0])[:3]:
                seen["rotate"] += 1
            else:
                seen["move"] += 1
        for kind in ("swap", "rotate", "move"):
            self.assertGreater(seen[kind], 500, kind)
        self.assertGreater(seen["remove"], 150)

    def test_seeded(self):
        state = random_state(PROBLEM, random.Random(2))
        a = [random_neighbor(state, random.Random(9)) for _ in range(5)]
        b = [random_neighbor(state, random.Random(9)) for _ in range(5)]
        self.assertEqual(a, b)

    def test_empty_state_falls_back_to_move(self):
        state = State(PROBLEM)
        rng = random.Random(3)
        for _ in range(100):
            changes = random_neighbor(state, rng)
            self.assertEqual(len(changes), 1)
            self.assertIsNotNone(changes[0][1])

    def test_single_loaded_vehicle_never_attempts_swap(self):
        singleton = parse_problem({
            "ships": [{"id": "D", "width": 2, "length": 2, "max_capacity": 5}],
            "vehicles": [{"id": "A", "width": 1, "length": 2,
                          "shipping_fee": 3, "weight": 1, "eta": 0}],
        })
        state = State(singleton, [(0, 0, 0, "H")])
        rng = random.Random(0)
        for _ in range(100):
            changes = random_neighbor(state, rng)
            self.assertEqual(len(changes), 1)
            self.assertEqual(changes[0][0], 0)


if __name__ == "__main__":
    unittest.main()
