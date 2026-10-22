"""Regresi kontrak pengguna: identitas hasil, objective replay, dan eksperimen terpisah."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from config import DATA_DIR
from core.eta_objective import eta_problem, run_eta
from core.problem import load_problem
from experiments import planned_runs
from main import run_algorithm, save_run, view_problem
from search.hill_climbing import steepest_ascent
from tests.test_cli import run_cli


class TestDeliveryBoundaries(unittest.TestCase):
    def test_dotted_instance_preserves_both_seed_results(self):
        problem = replace(load_problem(DATA_DIR / "small.json"), name="ferry.v2")
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for seed in (1, 2):
                result = run_algorithm("steepest", problem, seed).to_dict()
                paths.append(save_run(result, problem, tmp, plots=False)[0])
            self.assertNotEqual(paths[0], paths[1])
            self.assertEqual([json.loads(p.read_text())["seed"] for p in paths], [1, 2])
            self.assertTrue(all(p.stem.startswith("ferry.v2_") for p in paths))

    def test_eta_replay_transforms_explicit_original_input(self):
        path = DATA_DIR / "small.json"
        problem = load_problem(path)
        result = run_eta(steepest_ascent, problem, seed=1).to_dict()
        replay = view_problem(result, str(path))
        self.assertEqual(replay, eta_problem(problem))
        self.assertNotEqual(replay.vehicles[0].shipping_fee, problem.vehicles[0].shipping_fee)

    def test_eta_is_executable_from_main_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_cli("--algo", "sa", "--instance", "small", "--objective", "eta",
                                   "--iterations", "500", "--out", tmp, "--no-plot")
            self.assertEqual(code, 0, err)
            data = json.loads((Path(tmp) / "sa" / "small_eta_seed1.json").read_text())
            self.assertEqual(data["extra"]["objective"], "eta")
            self.assertTrue(data["is_feasible"])
            self.assertIn("shipping_fee_total", data["extra"])

    def test_invalid_algorithm_limits_are_cli_errors_not_tracebacks(self):
        for flags in (("--algo", "ga", "--population", 2),
                      ("--algo", "sideways", "--max-sideways", 0)):
            with self.subTest(flags=flags):
                code, _, _ = run_cli(*flags, "--no-save")
                self.assertEqual(code, 2)

    def test_ga_control_executions_have_separate_sweep_paths(self):
        plan = planned_runs()
        controls = [r for r in plan if r.algo == "ga" and r.params == {"population": 100, "iterations": 1000}]
        self.assertEqual(len(controls), 6)
        self.assertEqual(len({r.path(Path("output")) for r in controls}), 6)
        self.assertEqual({r.groups for r in controls}, {("ga_iter",), ("ga_pop",)})


if __name__ == "__main__":
    unittest.main()
