"""Test CLI `src/main.py`: tiap algoritma bisa dijalankan, hasil tersimpan dan bisa dibaca ulang, argumen salah ditolak."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from config import DATA_DIR, ROOT
from core.problem import load_problem
from core.eta_objective import run_eta
from main import ALGORITHMS, main, run_algorithm, run_id, save_run
from search.result import RunResult
from search.simulated_annealing import simulated_annealing

SMALL = load_problem(DATA_DIR / "small.json")
PNG_SIGNATURE = b"\x89PNG"
# parameter kecil supaya test cepat
QUICK = {
    "steepest": [],
    "sideways": ["--max-sideways", "5"],
    "random_restart": ["--max-restart", "1"],
    "stochastic": ["--max-no-improve", "200"],
    "sa": ["--iterations", "500"],
    "ga": ["--population", "10", "--iterations", "5"],
}


def run_cli(*argv):
    """Jalankan `main(argv)`, kembalikan (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = main([str(a) for a in argv])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


class TestRunAllAlgorithms(unittest.TestCase):
    def test_every_algorithm_saves_json_and_images(self):
        self.assertEqual(set(QUICK), set(ALGORITHMS))
        with tempfile.TemporaryDirectory() as tmp:
            for algo, params in QUICK.items():
                with self.subTest(algo=algo):
                    code, out, _ = run_cli("--algo", algo, "--instance", "small.json", "--seed", 2,
                                           "--out", tmp, *params)
                    self.assertEqual(code, 0)
                    folder = Path(tmp) / algo
                    stem = "small_pop10_iter5_seed2" if algo == "ga" else "small_seed2"
                    data = json.loads((folder / f"{stem}.json").read_text(encoding="utf-8"))
                    self.assertEqual((data["algorithm"], data["instance"], data["seed"]), (algo, "small", 2))
                    result = RunResult.from_dict(SMALL, data)
                    self.assertEqual(result.final_state.objective, data["final_objective"])
                    for suffix in ("initial", "final", "plot"):
                        self.assertEqual((folder / f"{stem}_{suffix}.png").read_bytes()[:4], PNG_SIGNATURE)
                    self.assertIn(f"akhir {data['final_objective']:g}", out)

    def test_params_reach_algorithm(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--algo", "random_restart", "--instance", "small", "--max-restart", 2, "--out", tmp,
                    "--no-plot")
            data = json.loads((Path(tmp) / "random_restart" / "small_seed1.json").read_text(encoding="utf-8"))
            self.assertEqual(data["params"]["max_restart"], 2)
            self.assertEqual(len(data["extra"]["iters_per_restart"]), 3)
            self.assertFalse(list((Path(tmp) / "random_restart").glob("*.png")))

    def test_max_iterations_limits_hill_climbing(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_cli("--algo", "steepest", "--instance", "multi", "--max-iterations", 1, "--out", tmp,
                                 "--no-plot")
            self.assertEqual(code, 0)
            data = json.loads((Path(tmp) / "steepest" / "multi_seed1.json").read_text(encoding="utf-8"))
            self.assertEqual(data["params"]["max_iterations"], 1)
            self.assertEqual(data["iterations"], 1)


class TestOptions(unittest.TestCase):
    def test_hc_is_alias_of_steepest(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, _ = run_cli("--algo", "hc", "--instance", "small", "--out", tmp, "--no-plot")
            self.assertEqual(code, 0)
            self.assertTrue((Path(tmp) / "steepest" / "small_seed1.json").is_file())

    def test_multi_ship_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run_cli("--algo", "ga", "--instance", "multi.json", "--population", 6,
                                   "--iterations", 2, "--out", tmp)
            self.assertEqual(code, 0)
            data = json.loads((Path(tmp) / "ga" / "multi_pop6_iter2_seed1.json").read_text(encoding="utf-8"))
            self.assertEqual(len(data["capacity"]), 3)
            self.assertEqual(len(data["final_state"]["decks"]), 3)
            self.assertEqual(out.count("Deck-"), 3)

    def test_no_save(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run_cli("--algo", "steepest", "--instance", "small", "--out", tmp, "--no-save")
            self.assertEqual(code, 0)
            self.assertEqual(list(Path(tmp).iterdir()), [])
            self.assertIn("Di luar kapal", out)

    def test_view_redraws_saved_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--algo", "sa", "--instance", "small", "--iterations", 300, "--out", tmp, "--no-plot")
            saved = Path(tmp) / "sa" / "small_seed1.json"
            code, out, _ = run_cli("--view", saved)
            self.assertEqual(code, 0)
            self.assertIn("algoritma   : sa | instance small | seed 1", out)
            self.assertTrue((Path(tmp) / "sa" / "small_seed1_plot.png").is_file())

    def test_view_eta_run(self):
        # hasil Bonus 1 (instance `small_eta`) dibuka dengan instance turunan bobot urgensi
        with tempfile.TemporaryDirectory() as tmp:
            result = run_eta(simulated_annealing, SMALL, seed=1, iterations=300)
            save_run(result.to_dict(), result.problem, tmp, plots=False)
            saved = Path(tmp) / "sa" / "small_eta_seed1.json"
            code, out, err = run_cli("--view", saved, "--no-plot")
            self.assertEqual(code, 0, err)
            self.assertIn("instance small_eta", out)
            self.assertIn(f"total fee   : {result.final_state.total_fee:g}", out)

    def test_invalid_arguments_exit_2(self):
        cases = [
            ("--algo", "sa", "--population", 10),           # parameter GA untuk SA
            ("--algo", "steepest", "--max-sideways", 5),    # parameter Sideways untuk Steepest
            ("--algo", "sa", "--max-iterations", 5),        # batas iterasi HC untuk SA (pakai --iterations)
            ("--algo", "ga", "--population", 0),
            ("--algo", "tabu"),
            ("--algo", "sa", "--objective", "eta"),        # Bonus 1 belum tersedia
            ("--algo", "sa", "--instance", "tidak_ada.json"),
            ("--seed", 1),                                  # tanpa --algo maupun --view
            ("--view", "tidak_ada.json"),
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, _, err = run_cli(*argv)
                self.assertEqual(code, 2)
                self.assertIn("error", err)

    def test_view_rejects_wrong_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--algo", "steepest", "--instance", "small", "--out", tmp, "--no-plot")
            code, _, err = run_cli("--view", Path(tmp) / "steepest" / "small_seed1.json", "--instance", "main.json")
            self.assertEqual(code, 2)
            self.assertIn("instance", err)

    def test_script_runs_from_repo_root(self):
        # `python src/main.py` (DESIGN §10): import absolut dari src/ harus jalan tanpa PYTHONPATH
        proc = subprocess.run([sys.executable, "src/main.py", "--help"], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--algo", proc.stdout)


class TestHelpers(unittest.TestCase):
    def test_run_algorithm_rejects_foreign_params(self):
        with self.assertRaises(ValueError):
            run_algorithm("sa", SMALL, 1, population=10)

    def test_run_id(self):
        result = run_algorithm("ga", SMALL, 3, population=4, iterations=1).to_dict()
        self.assertEqual(run_id(result), "small_pop4_iter1_seed3")
        self.assertEqual(run_id(dict(result, algorithm="sa")), "small_seed3")


if __name__ == "__main__":
    unittest.main()
