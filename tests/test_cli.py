"""Test kontrak CLI: hasil algoritma, artefak, replay, dan penolakan input."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from config import DATA_DIR
from core.problem import load_problem
from main import ALGORITHMS, main, run_algorithm
from search.result import RunResult

SMALL = load_problem(DATA_DIR / "small.json")
QUICK = {
    "steepest": [],
    "sideways": ["--max-sideways", "5"],
    "random_restart": ["--max-restart", "1"],
    "stochastic": ["--max-no-improve", "200"],
    "sa": ["--iterations", "500"],
    "ga": ["--population", "10", "--iterations", "5"],
}


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main([str(a) for a in argv])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class TestCliResults(unittest.TestCase):
    def test_every_algorithm_exports_valid_solution_and_visualizations(self):
        with tempfile.TemporaryDirectory() as tmp:
            for algo, params in QUICK.items():
                with self.subTest(algo=algo):
                    code, _, err = run_cli("--algo", algo, "--instance", "small.json", "--seed", 2,
                                           "--out", tmp, *params)
                    self.assertEqual(code, 0, err)
                    paths = list((Path(tmp) / algo).glob("*.json"))
                    self.assertEqual(len(paths), 1)
                    data = json.loads(paths[0].read_text())
                    result = RunResult.from_dict(SMALL, data)
                    self.assertTrue(result.final_state.is_feasible)
                    self.assertAlmostEqual(result.final_state.objective, data["final_objective"])
                    self.assertEqual(data["final_state"], result.final_state.to_dict())
                    for suffix in ("initial", "final", "plot"):
                        image = paths[0].with_name(paths[0].stem + "_" + suffix + ".png")
                        self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_hc_alias_has_same_solution_as_steepest(self):
        a = run_algorithm("hc", SMALL, 1)
        b = run_algorithm("steepest", SMALL, 1)
        self.assertEqual(a.final_state.positions, b.final_state.positions)
        self.assertEqual(a.history, b.history)

    def test_no_save_leaves_output_directory_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_cli("--algo", "steepest", "--instance", "small", "--out", tmp, "--no-save")
            self.assertEqual(code, 0, err)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_view_regenerates_images_without_changing_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--algo", "sa", "--instance", "small", "--iterations", 300, "--out", tmp, "--no-plot")
            path = Path(tmp) / "sa" / "small_seed1.json"
            before = path.read_bytes()
            code, _, err = run_cli("--view", path)
            self.assertEqual(code, 0, err)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(path.with_name(path.stem + "_final.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_multi_ship_output_has_matching_decks_and_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_cli("--algo", "ga", "--instance", "multi.json", "--population", 6,
                                   "--iterations", 2, "--out", tmp, "--no-plot")
            self.assertEqual(code, 0, err)
            path = Path(tmp) / "ga" / "multi_pop6_iter2_seed1.json"
            data = json.loads(path.read_text())
            problem = load_problem(DATA_DIR / "multi.json")
            result = RunResult.from_dict(problem, data)
            self.assertEqual(len(data["final_state"]["decks"]), len(problem.ships))
            self.assertEqual(data["capacity"], [ship.max_capacity for ship in problem.ships])
            self.assertTrue(result.final_state.is_feasible)

    def test_invalid_arguments_are_rejected(self):
        cases = [
            ("--algo", "sa", "--population", 10),
            ("--algo", "steepest", "--max-sideways", 5),
            ("--algo", "sa", "--max-iterations", 5),
            ("--algo", "ga", "--population", 0),
            ("--algo", "tabu"),
            ("--algo", "sa", "--instance", "tidak_ada.json"),
            ("--seed", 1),
            ("--view", "tidak_ada.json"),
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, _, _ = run_cli(*argv)
                self.assertEqual(code, 2)

    def test_view_rejects_different_input_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--algo", "steepest", "--instance", "small", "--out", tmp, "--no-plot")
            code, _, _ = run_cli("--view", Path(tmp) / "steepest" / "small_seed1.json", "--instance", "main.json")
            self.assertEqual(code, 2)

    def test_python_api_rejects_parameters_for_other_algorithm(self):
        with self.assertRaises(ValueError):
            run_algorithm("sa", SMALL, 1, population=10)


if __name__ == "__main__":
    unittest.main()
