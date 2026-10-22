"""Test format hasil run (RunResult) dan serialisasi state."""

import json
import random
import unittest

from config import DEFAULT_INSTANCE, SEEDS
from core.bounds import upper_bound
from core.problem import load_problem
from core.state import State, random_state
from search.result import RunResult

PROBLEM = load_problem(DEFAULT_INSTANCE)


def sample_result(**overrides):
    rng = random.Random(0)
    initial = random_state(PROBLEM, rng)
    final = State(PROBLEM, [(0, 0, 0, "H")] + [None] * (len(PROBLEM.vehicles) - 1))
    kwargs = dict(
        algorithm="steepest",
        seed=SEEDS[0],
        params={"max_iterations": 100},
        initial_state=initial,
        final_state=final,
        duration_s=0.5,
        iterations=2,
        evaluations=1234,
        history={"objective": [initial.objective, 0.0, final.objective], "prob": [[1, 0.25]]},
        extra={"stuck_count": 0},
    )
    kwargs.update(overrides)
    return RunResult(**kwargs)


class TestRunResult(unittest.TestCase):
    def test_derived_fields(self):
        result = sample_result()
        data = result.to_dict()
        vehicle = PROBLEM.vehicles[0]
        self.assertEqual(data["instance"], "main")
        self.assertEqual(data["final_objective"], vehicle.shipping_fee)
        self.assertEqual(data["total_fee"], vehicle.shipping_fee)
        self.assertTrue(data["is_feasible"])
        self.assertEqual(data["loaded"], 1)
        self.assertEqual(data["used_weight"], [vehicle.weight])
        self.assertAlmostEqual(data["used_area_pct"], 100 * vehicle.area / PROBLEM.ships[0].area)
        self.assertEqual(data["upper_bound"], upper_bound(PROBLEM))
        self.assertAlmostEqual(data["gap_ub"], 1 - vehicle.shipping_fee / upper_bound(PROBLEM))
        self.assertEqual(data["initial_objective"], result.initial_state.objective)

    def test_json_round_trip(self):
        result = sample_result()
        data = json.loads(json.dumps(result.to_dict()))
        restored = RunResult.from_dict(PROBLEM, data)
        self.assertEqual(restored.initial_state.positions, result.initial_state.positions)
        self.assertEqual(restored.final_state.positions, result.final_state.positions)
        self.assertEqual(restored.history, result.history)
        self.assertEqual(restored.to_dict(), data)

    def test_rejects_missing_objective_history(self):
        with self.assertRaises(ValueError):
            sample_result(history={"mean": []})

    def test_rejects_wrong_instance(self):
        data = sample_result().to_dict()
        data["instance"] = "small"
        with self.assertRaises(ValueError):
            RunResult.from_dict(PROBLEM, data)


class TestDeckGrid(unittest.TestCase):
    def test_grid_marks_vehicles_and_overlap(self):
        positions = [(0, 0, 0, "H"), (0, 0, 0, "H")] + [None] * (len(PROBLEM.vehicles) - 2)
        state = State(PROBLEM, positions)
        grid = state.to_dict()["decks"][0]["grid"]
        ship = PROBLEM.ships[0]
        self.assertEqual((len(grid), len(grid[0])), (ship.length, ship.width))
        a, b = PROBLEM.vehicles[0].id, PROBLEM.vehicles[1].id
        self.assertEqual(grid[0][0], f"{a}+{b}")
        filled = sum(cell != "" for row in grid for cell in row)
        self.assertEqual(filled, state.evaluate().occupied_cells[0])

    def test_from_dict_ignores_decks(self):
        state = random_state(PROBLEM, random.Random(4))
        self.assertEqual(State.from_dict(PROBLEM, state.to_dict()).positions, state.positions)


if __name__ == "__main__":
    unittest.main()
