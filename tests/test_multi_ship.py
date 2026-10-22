"""Test multi-kapal (Bonus 3): generator, neighbor lintas kapal, brute force, dan HC end-to-end."""

import itertools
import random
import unittest

from config import MULTI_INSTANCE
from core.bounds import brute_force, upper_bound
from core.generator import generate_instance
from core.problem import load_problem, parse_problem
from core.state import State
from search.hill_climbing import random_restart, sideways_move, steepest_ascent, stochastic
from search.neighbors import all_neighbors, all_placements, swap

FLEET = parse_problem(generate_instance(random.Random(5), 10, [(5, 6), (4, 4)], types=["motor", "sedan", "suv"]))


def per_ship_ok(state):
    """Cek constraint langsung per kapal dari grid: tidak ada overlap, berat <= kapasitas."""
    data = state.to_dict()
    for ship, deck in zip(state.problem.ships, data["decks"]):
        if any("+" in cell for row in deck["grid"] for cell in row):
            return False
        weight = sum(v.weight for v, p in zip(state.problem.vehicles, state.positions)
                     if p is not None and state.problem.ships[p[0]].id == ship.id)
        if weight > ship.max_capacity:
            return False
    return True


class TestFleetInstance(unittest.TestCase):
    def test_generator_builds_fleet(self):
        data = generate_instance(random.Random(1), 20, [(10, 12), (8, 10), (6, 8)])
        self.assertEqual([s["id"] for s in data["ships"]], ["Deck-1", "Deck-2", "Deck-3"])
        self.assertEqual([(s["width"], s["length"]) for s in data["ships"]], [(10, 12), (8, 10), (6, 8)])
        capacities = [s["max_capacity"] for s in data["ships"]]
        self.assertEqual(capacities, sorted(capacities, reverse=True))
        with self.assertRaises(ValueError):
            generate_instance(random.Random(1), 5, [])

    def test_multi_json(self):
        problem = load_problem(MULTI_INSTANCE)
        self.assertEqual(len(problem.ships), 3)
        self.assertEqual(len(problem.vehicles), 40)
        self.assertGreater(sum(v.area for v in problem.vehicles), sum(s.area for s in problem.ships))
        self.assertGreater(sum(v.weight for v in problem.vehicles), sum(s.max_capacity for s in problem.ships))


class TestFleetMoves(unittest.TestCase):
    def test_objective_is_total_fee_of_fleet(self):
        problem = parse_problem({
            "ships": [{"id": "A", "width": 3, "length": 3, "max_capacity": 4},
                      {"id": "B", "width": 2, "length": 2, "max_capacity": 4}],
            "vehicles": [{"id": "x", "width": 2, "length": 2, "shipping_fee": 10, "weight": 4, "eta": 1},
                         {"id": "y", "width": 2, "length": 2, "shipping_fee": 7, "weight": 4, "eta": 1}],
        })
        state = State(problem, [(0, 0, 0, "H"), (1, 0, 0, "H")])
        self.assertTrue(state.is_feasible)
        self.assertEqual(state.objective, 17)
        state.set(1, (0, 1, 1, "H"))
        self.assertFalse(state.is_feasible)

    def test_placements_cover_all_ships(self):
        placements = all_placements(FLEET)
        self.assertEqual(len(placements), 2 * (5 * 6 + 4 * 4))
        self.assertEqual({p[0] for p in placements}, {0, 1})

    def test_move_and_swap_across_ships(self):
        state = State(FLEET, [(0, 1, 1, "H"), (1, 2, 0, "V")] + [None] * (len(FLEET.vehicles) - 2))
        targets = {changes[0][1][0] for changes in all_neighbors(state)
                   if len(changes) == 1 and changes[0][0] == 0 and changes[0][1] is not None}
        self.assertEqual(targets, {0, 1})
        clone = state.copy()
        clone.apply(swap(state, 0, 1))
        self.assertEqual(clone.placement(0), (1, 2, 0, "H"))
        self.assertEqual(clone.placement(1), (0, 1, 1, "V"))


class TestFleetOptimum(unittest.TestCase):
    def test_brute_force_matches_exhaustive(self):
        problem = parse_problem({
            "ships": [{"id": "A", "width": 2, "length": 3, "max_capacity": 3},
                      {"id": "B", "width": 2, "length": 2, "max_capacity": 2}],
            "vehicles": [
                {"id": "p", "width": 1, "length": 2, "shipping_fee": 5, "weight": 2, "eta": 1},
                {"id": "q", "width": 2, "length": 2, "shipping_fee": 8, "weight": 2, "eta": 1},
                {"id": "r", "width": 1, "length": 3, "shipping_fee": 6, "weight": 1, "eta": 1},
            ],
        })
        options = [None, *all_placements(problem)]
        exhaustive = max(s.objective for positions in itertools.product(options, repeat=3)
                         if (s := State(problem, positions)).is_feasible)
        optimum = brute_force(problem)
        self.assertEqual(optimum.objective, exhaustive)
        self.assertTrue(per_ship_ok(optimum))
        self.assertGreaterEqual(upper_bound(problem), exhaustive)

    def test_hill_climbing_variants_on_fleet(self):
        optimum = brute_force(FLEET).objective
        runs = [
            steepest_ascent(FLEET, seed=1),
            sideways_move(FLEET, seed=1, max_sideways=20),
            random_restart(FLEET, seed=1, max_restart=3),
            stochastic(FLEET, seed=1, max_no_improve=3000),
        ]
        for result in runs:
            with self.subTest(result.algorithm):
                final = result.final_state
                self.assertTrue(final.is_feasible)
                self.assertTrue(per_ship_ok(final))
                self.assertLessEqual(final.objective, optimum)
                data = result.to_dict()
                self.assertEqual(len(data["used_weight"]), 2)
                self.assertEqual([len(d["grid"]) for d in data["final_state"]["decks"]], [6, 4])
        used_ships = {p[0] for p in runs[2].final_state.positions if p is not None}
        self.assertEqual(used_ships, {0, 1})


if __name__ == "__main__":
    unittest.main()
