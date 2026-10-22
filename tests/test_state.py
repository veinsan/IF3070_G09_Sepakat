"""Test objective dan delta evaluation pada State."""

import json
import math
import random
import unittest

from config import DATA_DIR
from core.objective import evaluate, weight_units
from core.problem import load_problem, parse_problem
from core.state import State, random_placement, random_state

DATA = DATA_DIR

# deck 4x4, kapasitas 10, berat minimum 3, P = 10 + 1 = 11
TINY = parse_problem({
    "ships": [{"id": "D", "width": 4, "length": 4, "max_capacity": 10}],
    "vehicles": [
        {"id": "A", "width": 2, "length": 2, "shipping_fee": 10, "weight": 4, "eta": 1},
        {"id": "B", "width": 1, "length": 3, "shipping_fee": 5, "weight": 3, "eta": 1},
        {"id": "C", "width": 1, "length": 1, "shipping_fee": 1, "weight": 5, "eta": 1},
    ],
})

# dua kapal + berat pecahan, untuk menguji agregat per kapal dan pembulatan weight_units
MULTI = parse_problem({
    "ships": [
        {"id": "D1", "width": 5, "length": 6, "max_capacity": 4.5},
        {"id": "D2", "width": 3, "length": 4, "max_capacity": 2},
    ],
    "vehicles": [
        {"id": f"M{i}", "width": 1 + i % 3, "length": 1 + i % 4, "shipping_fee": 3 + 2.5 * i,
         "weight": 0.5 + i % 3, "eta": 1}
        for i in range(10)
    ],
})


class TestObjective(unittest.TestCase):
    def test_hand_computed(self):
        state = State(TINY)
        self.assertEqual(state.objective, 0)
        self.assertTrue(state.is_feasible)

        state.set(0, (0, 0, 0, "H"))  # A di sel (0..1, 0..1)
        state.set(1, (0, 1, 0, "V"))  # B diputar: (1..3, 0), menimpa A di (1, 0)
        self.assertEqual(state.evaluate().overlap_cells, 1)
        self.assertEqual(state.objective, 15 - 11)

        state.set(1, (0, 3, 2, "H"))  # B di (3, 2..4): satu sel keluar geladak
        self.assertEqual(state.evaluate().out_of_bound_cells, 1)
        self.assertEqual(state.objective, 15 - 11)

        state.set(1, (0, 3, 1, "H"))  # B di (3, 1..3): feasible
        self.assertTrue(state.is_feasible)
        self.assertEqual(state.objective, 15)

        state.set(2, (0, 0, 3, "H"))  # berat 12 > 10, kelebihan 2 -> ceil(2 / 3) = 1 unit
        self.assertEqual(state.evaluate().weight_units, 1)
        self.assertEqual(state.objective, 16 - 11)
        self.assertFalse(state.is_feasible)

    def test_weight_units(self):
        self.assertEqual(weight_units(10, 10, 1), 0)
        self.assertEqual(weight_units(10 + 1e-12, 10, 1), 0)  # noise float bukan pelanggaran
        self.assertEqual(weight_units(11, 10, 1), 1)
        self.assertEqual(weight_units(10.25, 10, 0.5), 1)
        self.assertEqual(weight_units(11.5, 10, 0.5), 3)
        self.assertEqual(weight_units(1e12 + 1, 1e12, 1e12), 1)


class TestDeltaEvaluation(unittest.TestCase):
    def random_changes(self, state, rng):
        n = len(state.problem.vehicles)
        i, j = rng.sample(range(n), 2)
        kind = rng.randrange(4)
        if kind == 0:
            return [(i, random_placement(state.problem, rng))]
        if kind == 1:
            return [(i, None)]
        if kind == 2:
            return [(i, state.placement(j)), (j, state.placement(i))]  # tukar posisi
        placement = state.placement(i)
        if placement is None:
            return [(i, random_placement(state.problem, rng))]
        s, x, y, orientation = placement
        return [(i, (s, x, y, "V" if orientation == "H" else "H"))]  # rotate

    def test_matches_full_recompute(self):
        problems = [TINY, MULTI, load_problem(DATA / "main.json"), load_problem(DATA / "small.json")]
        for problem in problems:
            with self.subTest(problem.name or problem.vehicles[0].id):
                rng = random.Random(42)
                state = random_state(problem, rng)
                for _ in range(3000):
                    changes = self.random_changes(state, rng)
                    before_positions = state.positions
                    before = state.objective

                    predicted = state.delta(changes)
                    self.assertEqual(state.positions, before_positions, "delta() tidak boleh mengubah state")
                    self.assertTrue(math.isclose(state.objective, before, abs_tol=1e-9))

                    state.apply(changes)
                    self.assertTrue(math.isclose(state.objective - before, predicted, abs_tol=1e-9))

                    full = evaluate(problem, state.positions)
                    self.assertTrue(math.isclose(state.objective, full.objective, abs_tol=1e-9))
                    self.assertEqual(state.is_feasible, full.is_feasible)

    def test_infeasible_state_always_has_improving_removal(self):
        """Properti DESIGN §4: dari state infeasible, ada kendaraan yang jika dikeluarkan menaikkan f."""
        for problem in (load_problem(DATA / "main.json"), MULTI):
            rng = random.Random(7)
            for _ in range(300):
                state = random_state(problem, rng, p_inside=rng.random())
                if state.is_feasible:
                    continue
                loaded = [i for i, p in enumerate(state.positions) if p is not None]
                self.assertTrue(any(state.delta([(i, None)]) > 0 for i in loaded))


class TestStateUtilities(unittest.TestCase):
    def test_copy_is_independent(self):
        state = random_state(MULTI, random.Random(1))
        clone = state.copy()
        clone.set(0, None)
        clone.set(1, (1, 0, 0, "H"))
        self.assertEqual(state.objective, evaluate(MULTI, state.positions).objective)
        self.assertEqual(clone.objective, evaluate(MULTI, clone.positions).objective)

    def test_dict_round_trip(self):
        state = random_state(MULTI, random.Random(3))
        data = json.loads(json.dumps(state.to_dict()))  # harus bisa diserialisasi ke JSON
        restored = State.from_dict(MULTI, data)
        self.assertEqual(restored.positions, state.positions)
        self.assertEqual(restored.objective, state.objective)

    def test_random_state_is_seeded(self):
        a = random_state(MULTI, random.Random(5)).positions
        b = random_state(MULTI, random.Random(5)).positions
        self.assertEqual(a, b)

    def test_wrong_length_rejected(self):
        with self.assertRaises(ValueError):
            State(TINY, [None])


if __name__ == "__main__":
    unittest.main()
