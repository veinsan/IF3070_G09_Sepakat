"""Test visualisasi state dan plot hasil run (gambar dibuat ke folder sementara, tanpa GUI)."""

import random
import tempfile
import unittest
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg

from config import DATA_DIR, MULTI_INSTANCE
from core.problem import load_problem
from core.state import State, random_state
from search.hill_climbing import random_restart, steepest_ascent
from visualization.plots import plot_run, plot_summary
from visualization.state_view import draw_state, render_state_text, save_run_states

SMALL = load_problem(DATA_DIR / "small.json")
FLEET = load_problem(MULTI_INSTANCE)
PNG_SIGNATURE = b"\x89PNG"


def labels(fig):
    return [ax.get_label() for ax in fig.axes]


def texts(ax):
    return " ".join(t.get_text() for t in ax.texts)


class TestStateView(unittest.TestCase):
    def test_one_panel_per_ship_plus_outside(self):
        state = random_state(FLEET, random.Random(1)).to_dict()
        fig = draw_state(FLEET, state)
        self.assertEqual(labels(fig), [f"deck:{s.id}" for s in FLEET.ships] + ["outside"])

    def test_vehicles_inside_and_outside_are_shown(self):
        state = random_state(SMALL, random.Random(2))
        data = state.to_dict()
        fig = draw_state(SMALL, data)
        deck, outside = fig.axes
        for vehicle, placement in zip(SMALL.vehicles, state.positions):
            self.assertIn(vehicle.id, texts(deck if placement is not None else outside))
        self.assertIn(f"objective = {state.objective:g}", fig.get_suptitle())

    def test_violations_are_marked(self):
        # dua kendaraan pertama di anchor yang sama -> overlap, header menyebut tidak feasible
        positions = [(0, 0, 0, "H"), (0, 0, 0, "H")] + [None] * (len(SMALL.vehicles) - 2)
        fig = draw_state(SMALL, State(SMALL, positions).to_dict())
        self.assertIn("TIDAK feasible", fig.get_suptitle())
        hatched = [p for p in fig.axes[0].patches if p.get_hatch()]
        self.assertGreater(len(hatched), 0)

    def test_title_fits_figure(self):
        # state awal acak di geladak kecil: judul terpanjang (rincian pelanggaran) tetap muat di gambar
        for problem in (SMALL, FLEET):
            state = random_state(problem, random.Random(4)).to_dict()
            fig = draw_state(problem, state, title="Initial state | random_restart | small | seed 3")
            renderer = FigureCanvasAgg(fig).get_renderer()
            extent = fig._suptitle.get_window_extent(renderer)
            self.assertGreaterEqual(extent.x0, 0)
            self.assertLessEqual(extent.x1, fig.bbox.width)

    def test_render_text(self):
        state = random_state(FLEET, random.Random(3))
        text = render_state_text(FLEET, state.to_dict())
        for ship in FLEET.ships:
            self.assertIn(ship.id, text)
        outside = [v.id for v, p in zip(FLEET.vehicles, state.positions) if p is None]
        self.assertIn(", ".join(outside), text)
        # baris grid per kapal = panjang geladak
        grid_lines = [line for line in text.splitlines() if line and line[0] in ".V#"]
        self.assertEqual(len(grid_lines), sum(ship.length for ship in FLEET.ships))

    def test_save_run_states(self):
        result = steepest_ascent(SMALL, seed=1).to_dict()
        with tempfile.TemporaryDirectory() as tmp:
            paths = save_run_states(SMALL, result, Path(tmp) / "steepest" / "small_seed1")
            self.assertEqual([p.name for p in paths], ["small_seed1_initial.png", "small_seed1_final.png"])
            for path in paths:
                self.assertEqual(path.read_bytes()[:4], PNG_SIGNATURE)


class TestPlots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.steepest = steepest_ascent(SMALL, seed=1).to_dict()
        cls.restart = random_restart(SMALL, seed=1, max_restart=2).to_dict()

    def test_hill_climbing_plot(self):
        fig = plot_run(self.steepest)
        self.assertEqual(len(fig.axes), 1)
        lines = fig.axes[0].get_lines()
        self.assertEqual(list(lines[0].get_ydata()), self.steepest["history"]["objective"])

    def test_random_restart_shows_best(self):
        fig = plot_run(self.restart)
        legend = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertIn("terbaik sejauh ini", legend)

    def test_sa_adds_acceptance_plot(self):
        # format SA (EXPERIMENTS §2): history.prob = [iterasi, e^(ΔE/T)], extra.stuck_count
        result = dict(self.steepest, algorithm="sa", extra={"stuck_count": 3})
        result["history"] = {"objective": self.steepest["history"]["objective"], "prob": [[1, 0.9], [5, 0.4]]}
        fig = plot_run(result)
        self.assertEqual(len(fig.axes), 2)
        self.assertIn("stuck 3", fig.axes[1].get_title())
        self.assertEqual(fig.axes[1].collections[0].get_offsets().tolist(), [[1, 0.9], [5, 0.4]])

    def test_ga_plots_max_and_mean(self):
        result = dict(self.steepest, algorithm="ga", history={"objective": [1, 3, 4], "mean": [0, 2, 3]})
        fig = plot_run(result)
        legend = [t.get_text() for t in fig.axes[0].get_legend().get_texts()]
        self.assertIn("maksimum populasi", legend)
        self.assertIn("rata-rata populasi", legend)
        self.assertEqual(fig.axes[0].get_xlabel(), "generasi")

    def test_summary_and_saving(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.png"
            fig = plot_summary([self.steepest, self.restart], path)
            self.assertEqual(path.read_bytes()[:4], PNG_SIGNATURE)
            ticks = [t.get_text() for t in fig.axes[0].get_xticklabels()]
            self.assertEqual(ticks, ["steepest", "random_restart"])
            plot_run(self.steepest, Path(tmp) / "run" / "plot.png")
            self.assertTrue((Path(tmp) / "run" / "plot.png").exists())


if __name__ == "__main__":
    unittest.main()
