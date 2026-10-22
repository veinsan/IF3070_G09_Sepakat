"""Boundary regressions for feasible incumbents, budgets, and supplied instances."""

import unittest
from dataclasses import replace

from core.eta_objective import run_eta
from core.problem import parse_problem
from core.state import State
from search.genetic_algorithm import genetic_algorithm
from search.hill_climbing import random_restart, sideways_move, steepest_ascent, stochastic
from search.simulated_annealing import simulated_annealing


PROBLEM = parse_problem({
    "ships": [{"id": "D", "width": 2, "length": 1, "max_capacity": 10}],
    "vehicles": [
        {"id": "A", "width": 1, "length": 1, "shipping_fee": 100, "weight": 1, "eta": 0},
        {"id": "B", "width": 1, "length": 1, "shipping_fee": 100, "weight": 1, "eta": 1},
        {"id": "C", "width": 1, "length": 1, "shipping_fee": 100, "weight": 1, "eta": 2},
    ],
}, name="boundary")


def algorithms(budget):
    return (
        (steepest_ascent, {"max_iterations": budget}),
        (sideways_move, {"max_iterations": budget, "max_sideways": 2}),
        (random_restart, {"max_iterations": budget, "max_restart": 1}),
        (stochastic, {"max_iterations": budget}),
        (simulated_annealing, {"iterations": budget, "t0_samples": 0, "stuck_window": 1}),
    )


class TestSearchBoundaries(unittest.TestCase):
    def test_short_budgets_keep_raw_history_but_return_feasible(self):
        initial = State(PROBLEM, [(0, 0, 0, "H")] * 3)
        for budget in (0, 1):
            for algorithm, params in algorithms(budget):
                with self.subTest(algorithm=algorithm.__name__, budget=budget):
                    result = algorithm(PROBLEM, seed=0, initial=initial, **params)
                    self.assertTrue(result.final_state.evaluate().is_feasible)
                    self.assertEqual(result.history["objective"][0], 98)
                    self.assertEqual(result.history["best_feasible"][-1], result.final_state.objective)
                    self.assertEqual(result.history["evaluations"][-1], result.evaluations)
                    self.assertEqual(len(result.history["evaluations"]), result.iterations + 1)
                    self.assertEqual(initial.positions, ((0, 0, 0, "H"),) * 3)
                    if budget == 0 and algorithm is not random_restart:
                        self.assertTrue(result.extra["empty_baseline_used"])
                        self.assertFalse(result.extra["found_feasible"])
                        self.assertFalse(result.extra["raw_final_is_feasible"])
                        self.assertEqual(result.final_state.positions, (None, None, None))

    def test_initial_must_match_problem_content(self):
        other = replace(PROBLEM, vehicles=(replace(PROBLEM.vehicles[0], shipping_fee=1), *PROBLEM.vehicles[1:]))
        for algorithm, params in algorithms(0):
            with self.subTest(algorithm=algorithm.__name__), self.assertRaises(ValueError):
                algorithm(PROBLEM, initial=State(other), **params)

    def test_equal_problem_initial_is_rebound_without_mutating_it(self):
        equal = replace(PROBLEM)
        for algorithm, params in algorithms(0):
            with self.subTest(algorithm=algorithm.__name__):
                initial = State(equal)
                result = algorithm(PROBLEM, initial=initial, **params)
                self.assertIs(result.initial_state.problem, PROBLEM)
                self.assertIs(result.final_state.problem, PROBLEM)
                self.assertIs(initial.problem, equal)

    def test_eta_rebinds_supplied_initial_before_search(self):
        initial = State(PROBLEM, [(0, 0, 0, "H"), None, None])
        result = run_eta(steepest_ascent, PROBLEM, initial=initial, max_iterations=1, seed=0)
        self.assertEqual(result.initial_state.objective, 200)
        self.assertAlmostEqual(result.final_state.objective, 350)
        self.assertEqual(result.extra["shipping_fee_total"], 200)
        self.assertEqual(initial.objective, 100)
        self.assertEqual(result.problem.name, "boundary_eta")

    def test_ga_keeps_feasible_individual_even_when_infeasible_raw_best_is_higher(self):
        result = genetic_algorithm(PROBLEM, population_size=2, elitism=0, iterations=0, seed=8)
        self.assertEqual(result.history["objective"], [199])
        self.assertEqual(result.history["best_feasible"], [100])
        self.assertTrue(result.final_state.is_feasible)
        self.assertEqual(result.final_state.objective, 100)
        self.assertFalse(result.extra["empty_baseline_used"])

    def test_ga_no_feasible_population_discloses_baseline(self):
        for budget in (0, 1):
            with self.subTest(budget=budget):
                result = genetic_algorithm(PROBLEM, population_size=2, elitism=0, iterations=budget,
                                           p_crossover=0, p_mutation=0, seed=4)
                self.assertTrue(result.final_state.is_feasible)
                self.assertTrue(result.extra["empty_baseline_used"])
                self.assertEqual(result.history["objective"], [99] * (budget + 1))
                self.assertEqual(result.history["best_feasible"], [0] * (budget + 1))
                self.assertEqual(result.history["evaluations"], [2 * (k + 1) for k in range(budget + 1)])

    def test_hc_final_neighborhood_is_in_evaluation_history(self):
        tiny = replace(PROBLEM, vehicles=PROBLEM.vehicles[:1])
        initial = State(tiny, [(0, 0, 0, "H")])
        result = steepest_ascent(tiny, initial=initial)
        self.assertEqual(result.iterations, 0)
        self.assertEqual(result.history["evaluations"], [4])

    def test_sa_keeps_feasible_visit_below_raw_best(self):
        raw = State(PROBLEM, [(0, 0, 0, "H"), (0, 1, 0, "H"), (0, 0, 0, "H")])
        result = simulated_annealing(PROBLEM, initial=raw, seed=586, iterations=2,
                                     t0_samples=1, stuck_window=10)
        self.assertEqual(result.history["objective"], [199, 99, 100])
        self.assertEqual(result.extra["raw_best_objective"], 199)
        self.assertEqual(result.history["best_feasible"], [0, 0, 100])
        self.assertTrue(result.final_state.is_feasible)
        self.assertEqual(result.final_state.objective, 100)

    def test_restart_offsets_terminal_neighborhood_counts(self):
        tiny = replace(PROBLEM, vehicles=PROBLEM.vehicles[:1])
        initial = State(tiny, [(0, 0, 0, "H")])
        result = random_restart(tiny, initial=initial, max_restart=1, seed=0)
        self.assertEqual(result.history["evaluations"], [4, 5, 12])
        self.assertEqual(result.evaluations, 12)
        self.assertEqual(result.iterations, 2)

    def test_singleton_searches_accept_one_iteration(self):
        tiny = replace(PROBLEM, vehicles=PROBLEM.vehicles[:1])
        initial = State(tiny, [(0, 0, 0, "H")])
        for algorithm, params in algorithms(1):
            with self.subTest(algorithm=algorithm.__name__):
                result = algorithm(tiny, initial=initial, seed=0, **params)
                self.assertTrue(result.final_state.is_feasible)
        result = genetic_algorithm(tiny, population_size=2, elitism=0, iterations=1,
                                   p_mutation=1, seed=0)
        self.assertTrue(result.final_state.is_feasible)


if __name__ == "__main__":
    unittest.main()
