"""Regresi runner: cakupan eksperimen, isolasi sweep, replay gambar, dan resume."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from config import SEEDS
from experiments import GROUPS, comparison_groups, load_results, main, planned_runs
from main import view_problem
from search.result import RunResult


def run_cli(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main([str(a) for a in argv])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue()


class TestExperimentCoverage(unittest.TestCase):
    def test_both_ga_sweeps_execute_every_configuration_three_times(self):
        plan = planned_runs()
        self.assertEqual(sum(run.required for run in plan), 24)
        self.assertEqual(len(plan), 39)
        self.assertEqual(len({run.path(Path("output")) for run in plan}), 39)
        for group in ("ga_iter", "ga_pop"):
            runs = [run for run in plan if group in run.groups]
            settings = {(run.params["population"], run.params["iterations"]) for run in runs}
            self.assertEqual(len(settings), 3)
            for population, iterations in settings:
                self.assertEqual(sorted(run.seed for run in runs if run.params == {
                    "population": population, "iterations": iterations}), list(SEEDS))
        self.assertEqual({run.groups[0] for run in plan}, set(GROUPS))

    def test_dry_run_has_no_filesystem_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("--dry-run", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_quick_run_produces_complete_feasible_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("--quick", "--no-plot", "--out", tmp)
            self.assertEqual(code, 0)
            plan = planned_runs(quick=True)
            pairs = load_results(plan, Path(tmp))
            self.assertEqual(len(pairs), 39)
            self.assertEqual(set(Path(tmp).rglob("*.json")), {run.path(Path(tmp)) for run in plan})
            for run, data in pairs:
                result = RunResult.from_dict(view_problem(data, str(run.instance)), data)
                self.assertTrue(result.final_state.is_feasible)
                self.assertAlmostEqual(result.final_state.objective, data["final_objective"])
                self.assertEqual(len(data["history"]["objective"]), data["iterations"] + 1)
            self.assertTrue((Path(tmp) / "summary.md").is_file())
            self.assertTrue((Path(tmp) / "summary_eta.md").is_file())
            groups = comparison_groups(pairs)
            self.assertTrue(all(len(results) == 3 for results in groups.values()))
            self.assertFalse(list(Path(tmp).rglob("*.png")))

    def test_plots_only_preserves_search_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("--quick", "--only", "sa", "--out", tmp)
            self.assertEqual(code, 0)
            runs = [run for run in planned_runs(quick=True) if "sa" in run.groups]
            before = {run.path(Path(tmp)): run.path(Path(tmp)).read_bytes() for run in runs}
            image = runs[0].path(Path(tmp)).with_name(runs[0].run_id + "_plot.png")
            image.unlink()
            code, _ = run_cli("--quick", "--plots-only", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            self.assertEqual(image.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_resume_preserves_completed_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--quick", "--only", "hc", "--no-plot", "--out", tmp)
            runs = [run for run in planned_runs(quick=True) if "hc" in run.groups]
            before = {run.path(Path(tmp)): run.path(Path(tmp)).read_bytes() for run in runs}
            code, _ = run_cli("--quick", "--only", "hc", "--skip-existing", "--no-plot", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertEqual({path: path.read_bytes() for path in before}, before)


if __name__ == "__main__":
    unittest.main()
