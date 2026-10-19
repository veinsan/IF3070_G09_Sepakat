"""Test upper bound (relaksasi knapsack) dan brute force global optimum."""

import itertools
import math
import random
import unittest
from pathlib import Path

from core.bounds import brute_force, fits_somewhere, gap, upper_bound
from core.generator import generate_instance
from core.problem import load_problem, parse_problem
from core.state import State
from search.neighbors import all_placements

DATA = Path(__file__).resolve().parent.parent / "src" / "data"


def random_problems(count, n, width, length, seed, types=("motor", "sedan", "suv")):
    rng = random.Random(seed)
    for _ in range(count):
        data = generate_instance(rng, n, [(width, length)], rng.choice([0.6, 1.0, 3.0]), list(types))
        yield parse_problem(data)


def relaxation_by_subsets(problem):
    """Acuan UB: coba semua subset kendaraan terhadap batas luas dan berat (floor)."""
    area_cap = sum(s.area for s in problem.ships)
    weight_cap = math.floor(sum(s.max_capacity for s in problem.ships))
    candidates = [v for v in problem.vehicles if fits_somewhere(problem, v)]
    best = 0
    for mask in range(1 << len(candidates)):
        chosen = [v for k, v in enumerate(candidates) if mask >> k & 1]
        if sum(v.area for v in chosen) <= area_cap and sum(math.floor(v.weight) for v in chosen) <= weight_cap:
            best = max(best, sum(v.shipping_fee for v in chosen))
    return best


class TestUpperBound(unittest.TestCase):
    def test_matches_subset_enumeration(self):
        for problem in random_problems(15, 9, 4, 5, seed=1):
            self.assertEqual(upper_bound(problem), relaxation_by_subsets(problem))

    def test_ignores_vehicle_that_never_fits(self):
        problem = parse_problem({
            "ships": [{"id": "D", "width": 4, "length": 6, "max_capacity": 100}],
            "vehicles": [
                {"id": "big", "width": 3, "length": 9, "shipping_fee": 500, "weight": 1, "eta": 1},
                {"id": "rot", "width": 6, "length": 2, "shipping_fee": 10, "weight": 1, "eta": 1},  # muat jika V
            ],
        })
        self.assertFalse(fits_somewhere(problem, problem.vehicles[0]))
        self.assertTrue(fits_somewhere(problem, problem.vehicles[1]))
        self.assertEqual(upper_bound(problem), 10)

    def test_valid_for_fractional_weights(self):
        problem = parse_problem({
            "ships": [{"id": "D", "width": 4, "length": 4, "max_capacity": 1.5}],
            "vehicles": [{"id": f"F{i}", "width": 1, "length": 2, "shipping_fee": 5, "weight": 0.5, "eta": 1}
                         for i in range(6)],
        })
        optimum = brute_force(problem)
        self.assertEqual(optimum.objective, 15)  # hanya 3 kendaraan seberat 0.5 yang muat di kapasitas 1.5
        self.assertGreaterEqual(upper_bound(problem), optimum.objective)

    def test_gap(self):
        self.assertAlmostEqual(gap(90, 100), 0.1)
        self.assertEqual(gap(0, 0), 0.0)


class TestBruteForce(unittest.TestCase):
    def test_matches_exhaustive_search(self):
        """Bandingkan dengan enumerasi seluruh state (semua placement atau di luar) pada instance mungil."""
        for problem in random_problems(4, 3, 4, 4, seed=2, types=("motor", "sedan")):
            options = [None, *all_placements(problem)]
            exhaustive = max(
                state.objective
                for positions in itertools.product(options, repeat=len(problem.vehicles))
                if (state := State(problem, positions)).is_feasible
            )
            self.assertEqual(brute_force(problem).objective, exhaustive)

    def test_optimum_feasible_and_below_bound(self):
        for problem in random_problems(10, 8, 5, 6, seed=3):
            optimum = brute_force(problem)
            self.assertTrue(optimum.is_feasible)
            self.assertEqual(optimum.objective, optimum.total_fee)
            self.assertGreaterEqual(upper_bound(problem), optimum.objective)

    def test_small_instance_reference_values(self):
        """Nilai acuan small.json yang dipakai di laporan (DESIGN §6)."""
        problem = load_problem(DATA / "small.json")
        self.assertEqual(brute_force(problem).objective, 287)
        self.assertEqual(upper_bound(problem), 298)

    def test_node_limit(self):
        with self.assertRaises(RuntimeError):
            brute_force(load_problem(DATA / "main.json"), max_nodes=1000)


if __name__ == "__main__":
    unittest.main()
