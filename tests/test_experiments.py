"""Test runner eksperimen `src/experiments.py` (hasil ditulis ke folder sementara, bukan output/)."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from config import SEEDS
from experiments import GROUPS, main, planned_runs
from main import run_id

PNG_SIGNATURE = b"\x89PNG"


def run_cli(*argv):
    """Jalankan `experiments.main(argv)`, kembalikan (exit code, stdout)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main([str(a) for a in argv])
        except SystemExit as e:
            code = e.code
    return code, out.getvalue()


def json_files(folder):
    return sorted(p.relative_to(folder).as_posix() for p in Path(folder).rglob("*.json"))


class TestPlannedRuns(unittest.TestCase):
    def test_counts_and_unique_ids(self):
        for quick in (False, True):
            with self.subTest(quick=quick):
                runs = planned_runs(quick=quick)
                self.assertEqual(sum(r.required for r in runs), 21)
                self.assertEqual(len(runs), 36)
                paths = [(r.algo, r.run_id) for r in runs]
                self.assertEqual(len(paths), len(set(paths)))
                self.assertTrue(all(r.seed in SEEDS for r in runs))

    def test_groups(self):
        runs = planned_runs()
        size = {g: sum(g in r.groups for r in runs) for g in GROUPS}
        self.assertEqual(size, {"hc": 3, "sa": 3, "ga_iter": 9, "ga_pop": 9, "hc_variants": 9, "eta": 3, "multi": 3})
        # konfigurasi kontrol GA dipakai bersama oleh kedua tabel GA
        shared = [r for r in runs if set(r.groups) == {"ga_iter", "ga_pop"}]
        self.assertEqual({r.run_id for r in shared}, {f"main_pop100_iter1000_seed{s}" for s in SEEDS})
        self.assertTrue(all(r.instance.name == "multi.json" for r in runs if "multi" in r.groups))

    def test_eta_is_skipped_until_available(self):
        eta = [r for r in planned_runs() if "eta" in r.groups]
        self.assertEqual(len(eta), 3)
        self.assertFalse(any(r.available for r in eta))
        self.assertTrue(all("_eta_" in r.run_id for r in eta))

    def test_run_id_matches_cli(self):
        # nama file dari rencana harus sama dengan nama file yang ditulis main.save_run
        for run in planned_runs():
            result = {"algorithm": run.algo, "instance": run.instance.stem, "seed": run.seed, "params": run.params}
            if run.objective == "fee":
                self.assertEqual(run.run_id, run_id(result))


class TestRunner(unittest.TestCase):
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run_cli("--dry-run", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertIn("21 run wajib, 36 run dengan bonus (3 dilewati", out)
            listed = [line.split()[3] for line in out.splitlines()[1:]]
            algos = [line.split()[1] for line in out.splitlines()[1:]]
            self.assertEqual(len(listed), 36)
            self.assertEqual(len(set(zip(algos, listed))), 36)
            self.assertEqual(list(Path(tmp).iterdir()), [])

            code, out = run_cli("--dry-run", "--only", "ga_pop", "--out", tmp)
            self.assertEqual(len(out.splitlines()) - 1, 9)

    def test_quick_run_writes_json_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("--quick", "--no-plot", "--out", tmp)
            self.assertEqual(code, 0)
            expected = sorted(f"{r.algo}/{r.run_id}.json" for r in planned_runs(quick=True) if r.available)
            self.assertEqual(json_files(tmp), expected)
            self.assertEqual(len(expected), 33)
            summary = (Path(tmp) / "summary.md").read_text(encoding="utf-8")
            # satu tabel per bagian EXPERIMENTS §4.1-§4.9
            for k in range(1, 10):
                self.assertIn(f"### 4.{k} ", summary)
            self.assertIn("small_eta_seed1", summary)  # run ETA tercatat sebagai belum ada
            self.assertFalse(list(Path(tmp).rglob("*.png")))

    def test_quick_run_with_images_and_plots_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _ = run_cli("--quick", "--only", "sa", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertEqual(json_files(tmp), [f"sa/small_seed{s}.json" for s in SEEDS])
            for s in SEEDS:
                for suffix in ("initial", "final", "plot"):
                    image = Path(tmp) / "sa" / f"small_seed{s}_{suffix}.png"
                    self.assertEqual(image.read_bytes()[:4], PNG_SIGNATURE)
            self.assertTrue((Path(tmp) / "summary_algorithms.png").is_file())
            self.assertIn("summary_algorithms.png", (Path(tmp) / "summary.md").read_text(encoding="utf-8"))

            # --plots-only menggambar ulang dari JSON tanpa menjalankan search
            image = Path(tmp) / "sa" / "small_seed1_plot.png"
            image.unlink()
            before = (Path(tmp) / "sa" / "small_seed1.json").read_text(encoding="utf-8")
            code, out = run_cli("--quick", "--plots-only", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertIn("3 run digambar ulang", out)
            self.assertTrue(image.is_file())
            self.assertEqual((Path(tmp) / "sa" / "small_seed1.json").read_text(encoding="utf-8"), before)

    def test_skip_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_cli("--quick", "--only", "hc", "--no-plot", "--out", tmp)
            path = Path(tmp) / "steepest" / "small_seed1.json"
            # tandai file lama: bila dijalankan ulang, penanda ini hilang
            data = json.loads(path.read_text(encoding="utf-8"))
            data["extra"]["marker"] = "lama"
            path.write_text(json.dumps(data), encoding="utf-8")

            code, out = run_cli("--quick", "--only", "hc", "--skip-existing", "--no-plot", "--out", tmp)
            self.assertEqual(code, 0)
            self.assertEqual(out.count("sudah ada, dilewati"), 3)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["extra"]["marker"], "lama")

            code, out = run_cli("--quick", "--only", "hc", "--skip-existing", "--dry-run", "--out", tmp)
            self.assertEqual(out.count("sudah ada"), 3)

            # tanpa --skip-existing run dijalankan ulang dan menimpa file
            run_cli("--quick", "--only", "hc", "--no-plot", "--out", tmp)
            self.assertNotIn("marker", json.loads(path.read_text(encoding="utf-8"))["extra"])


if __name__ == "__main__":
    unittest.main()
