"""Test objective urgensi ETA (Bonus 1): bobot, instance turunan, penalty, delta evaluation, dan run."""

import random
import unittest

from config import DATA_DIR
from core.bounds import upper_bound
from core.eta_objective import eta_problem, run_eta, shipping_fee_total, urgency_weight
from core.objective import evaluate, penalty_coefficient
from core.problem import load_problem, parse_problem
from core.state import State, random_state
from search.genetic_algorithm import genetic_algorithm
from search.hill_climbing import steepest_ascent
from search.neighbors import random_neighbor
from search.simulated_annealing import simulated_annealing

DATA = DATA_DIR
MAIN = load_problem(DATA / "main.json")
SMALL = load_problem(DATA / "small.json")
MULTI = load_problem(DATA / "multi.json")

# deck 4x4, kapasitas 10. Bobot: A = 10 · (1 + 1/1) = 20, B = 6 · (1 + 1/3) = 8, C = 4 · (1 + 1/5) = 4.8
TINY = parse_problem({
    "ships": [{"id": "D", "width": 4, "length": 4, "max_capacity": 10}],
    "vehicles": [
        {"id": "A", "width": 2, "length": 2, "shipping_fee": 10, "weight": 4, "eta": 0},
        {"id": "B", "width": 1, "length": 3, "shipping_fee": 6, "weight": 3, "eta": 2},
        {"id": "C", "width": 1, "length": 1, "shipping_fee": 4, "weight": 5, "eta": 4},
    ],
}, name="tiny")

SA_PARAMS = {"iterations": 3000, "t0_samples": 100}


class TestUrgencyWeight(unittest.TestCase):
    def test_hand_computed(self):
        self.assertEqual([urgency_weight(v) for v in TINY.vehicles], [20, 8, 4.8])

    def test_more_urgent_weighs_more(self):
        a, b, c = TINY.vehicles
        weights = [urgency_weight(v) / v.shipping_fee for v in (a, b, c)]
        self.assertEqual(weights, sorted(weights, reverse=True))
        for v in MAIN.vehicles:
            self.assertGreater(urgency_weight(v), v.shipping_fee)
            self.assertLessEqual(urgency_weight(v), 2 * v.shipping_fee)


class TestEtaProblem(unittest.TestCase):
    def test_only_fee_and_name_change(self):
        derived = eta_problem(MAIN)
        self.assertEqual(derived.name, "main_eta")
        self.assertEqual(derived.ships, MAIN.ships)
        for old, new in zip(MAIN.vehicles, derived.vehicles, strict=True):
            self.assertEqual((new.id, new.width, new.length, new.weight, new.eta),
                             (old.id, old.width, old.length, old.weight, old.eta))
            self.assertEqual(new.shipping_fee, urgency_weight(old))
        # instance asli tidak berubah
        self.assertEqual(MAIN.name, "main")
        self.assertEqual(MAIN.vehicles[0].shipping_fee, 48)

    def test_penalty_uses_max_weight(self):
        self.assertEqual(penalty_coefficient(eta_problem(TINY)), 21)

    def test_objective_is_total_weight(self):
        positions = [(0, 0, 0, "H"), (0, 2, 0, "H"), None]  # A dan B dimuat, feasible
        state = State(eta_problem(TINY), positions)
        self.assertTrue(state.is_feasible)
        self.assertEqual(state.objective, 28)
        self.assertEqual(shipping_fee_total(TINY, positions), 16)

    def test_violation_penalised_with_weight_based_p(self):
        # A dan C overlap satu sel, berat 9 <= 10
        state = State(eta_problem(TINY), [(0, 0, 0, "H"), None, (0, 1, 1, "H")])
        self.assertEqual(state.objective, 20 + 4.8 - 21 * 1)


class TestDeltaEvaluation(unittest.TestCase):
    def test_delta_matches_full_recompute(self):
        for problem in (eta_problem(MAIN), eta_problem(MULTI)):
            rng = random.Random(5)
            state = random_state(problem, rng)
            for _ in range(2000):
                changes = random_neighbor(state, rng)
                d = state.delta(changes)
                before = state.objective
                state.apply(changes)
                self.assertAlmostEqual(state.objective - before, d, places=6)
                self.assertAlmostEqual(state.objective, evaluate(problem, state.positions).objective, places=6)

    def test_infeasible_state_has_improving_removal(self):
        problem = eta_problem(MAIN)
        rng = random.Random(9)
        checked = 0
        for _ in range(200):
            state = random_state(problem, rng, p_inside=0.8)
            if state.is_feasible:
                continue
            checked += 1
            inside = [i for i, p in enumerate(state.positions) if p is not None]
            self.assertTrue(any(state.delta([(i, None)]) > 0 for i in inside))
        self.assertGreater(checked, 0)


class TestRunEta(unittest.TestCase):
    def test_sa_run(self):
        result = run_eta(simulated_annealing, SMALL, seed=1, **SA_PARAMS)
        data = result.to_dict()
        self.assertEqual(data["instance"], "small_eta")
        self.assertTrue(data["is_feasible"])
        self.assertEqual(result.extra["objective"], "eta")
        self.assertEqual(result.extra["shipping_fee_total"],
                         shipping_fee_total(SMALL, result.final_state.positions))
        # final objective = total bobot, dan UB dihitung dengan bobot yang sama
        self.assertAlmostEqual(data["final_objective"], data["total_fee"])
        self.assertEqual(data["upper_bound"], upper_bound(eta_problem(SMALL)))
        self.assertLessEqual(data["final_objective"], data["upper_bound"] + 1e-9)
        self.assertGreaterEqual(data["gap_ub"], -1e-12)

    def test_same_seed_same_initial_positions_as_fee_run(self):
        fee = simulated_annealing(SMALL, seed=2, **SA_PARAMS)
        eta = run_eta(simulated_annealing, SMALL, seed=2, **SA_PARAMS)
        self.assertEqual(fee.initial_state.positions, eta.initial_state.positions)

    def test_ga_run(self):
        result = run_eta(genetic_algorithm, SMALL, seed=3, population_size=10, iterations=20)
        self.assertTrue(result.final_state.is_feasible)
        self.assertEqual(result.problem.name, "small_eta")

    def test_supplied_initial_uses_transformed_objective(self):
        initial = State(TINY, [(0, 0, 0, "H"), (0, 2, 0, "H"), None])
        result = run_eta(steepest_ascent, TINY, initial=initial, max_iterations=0)
        self.assertEqual(result.initial_state.objective, 28)
        self.assertEqual(result.final_state.objective, 28)
        self.assertEqual(result.extra["shipping_fee_total"], 16)
        self.assertEqual(initial.objective, 16)

    def test_mismatched_initial_is_rejected(self):
        with self.assertRaises(ValueError):
            run_eta(steepest_ascent, TINY, initial=State(SMALL), max_iterations=0)




if __name__ == "__main__":
    unittest.main()
