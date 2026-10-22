"""Real search traces must observe, never alter optimization or retain mutable states."""

import unittest

from config import DATA_DIR
from core.eta_objective import eta_problem
from core.problem import load_problem, parse_problem
from core.state import State
from search.genetic_algorithm import genetic_algorithm
from search.hill_climbing import random_restart, sideways_move, steepest_ascent, stochastic
from search.simulated_annealing import simulated_annealing
from search.trace import TraceRecorder

SMALL = load_problem(DATA_DIR / "small.json")
CASES = (
    (steepest_ascent, {"max_iterations": 8}),
    (sideways_move, {"max_iterations": 12, "max_sideways": 5}),
    (random_restart, {"max_iterations": 8, "max_restart": 2}),
    (stochastic, {"max_iterations": 100, "max_no_improve": 40}),
    (simulated_annealing, {"iterations": 100, "t0_samples": 10, "stuck_window": 25}),
    (genetic_algorithm, {"iterations": 12, "population_size": 8}),
)


class TestSearchObserver(unittest.TestCase):
    def test_observation_preserves_search_and_matches_current_history(self):
        for problem in (SMALL, eta_problem(SMALL)):
            for function, params in CASES:
                with self.subTest(problem=problem.name, algorithm=function.__name__):
                    expected = function(problem, seed=3, **params)
                    seen = []
                    trace = TraceRecorder(max_frames=12)

                    def observe(step, current, best, details=None):
                        trace(step, current, best, details)
                        seen.append((step, current.objective, best.positions, dict(details or {}),
                                     best.objective, best.is_feasible))

                    actual = function(problem, seed=3, observer=observe, **params)
                    self.assertEqual(actual.history, expected.history)
                    self.assertEqual(actual.final_state.positions, expected.final_state.positions)
                    self.assertEqual(actual.evaluations, expected.evaluations)
                    self.assertEqual(actual.extra, expected.extra)
                    self.assertEqual(seen[0][0], 0)
                    self.assertEqual(seen[-1][0], actual.iterations)
                    self.assertEqual(seen[-1][2], actual.final_state.positions)
                    self.assertEqual(seen[-1][3]["event"], "finished")
                    self.assertEqual([row[0] for row in seen], sorted(row[0] for row in seen))
                    for step, value, _, _, best_value, feasible in seen:
                        self.assertAlmostEqual(value, actual.history["objective"][step])
                        self.assertAlmostEqual(best_value, actual.history["best_feasible"][step])
                        self.assertTrue(feasible)

    def test_zero_budget_retains_initial_and_final(self):
        for function, params in CASES:
            params = {**params}
            if "iterations" in params:
                params["iterations"] = 0
            else:
                params["max_iterations"] = 0
            trace = TraceRecorder()
            result = function(SMALL, seed=3, observer=trace, **params)
            with self.subTest(algorithm=function.__name__):
                self.assertEqual(trace.frames[0]["step"], 0)
                self.assertEqual(trace.frames[-1]["step"], result.iterations)
                self.assertEqual(trace.frames[-1]["best"]["positions"],
                                 [list(p) if p is not None else None for p in result.final_state.positions])


class TestTraceRecorder(unittest.TestCase):
    def test_bounded_snapshots_are_detached_and_keep_first_and_final(self):
        problem = parse_problem({
            "ships": [{"id": "A", "width": 1, "length": 1, "max_capacity": 2}],
            "vehicles": [{"id": "V", "width": 1, "length": 1,
                          "shipping_fee": 10, "weight": 1, "eta": 0}],
        })
        state = State(problem)
        trace = TraceRecorder(max_frames=12)
        trace(0, state, state)
        for step in range(1, 500):
            state.set(0, (0, 0, 0, "H") if step % 2 else None)
            trace(step, state, state)
        trace(499, state, state, {"event": "finished"})
        state.set(0, None)
        self.assertLessEqual(len(trace.frames), 12)
        self.assertEqual(trace.frames[0]["step"], 0)
        self.assertEqual(trace.frames[0]["current"]["positions"], [None])
        self.assertEqual(trace.frames[-1]["step"], 499)
        self.assertEqual(trace.frames[-1]["current"]["positions"], [[0, 0, 0, "H"]])
        self.assertEqual(trace.frames[-1]["current"]["objective"], 10)
        steps = [frame["step"] for frame in trace.frames]
        self.assertEqual(steps, sorted(set(steps)))
        for frame in trace.frames:
            evaluation = State(problem, frame["current"]["positions"]).evaluate()
            self.assertEqual(frame["current"]["objective"], evaluation.objective)
            self.assertEqual(frame["current"]["feasible"], evaluation.is_feasible)


if __name__ == "__main__":
    unittest.main()
