"""Test loader, validasi instance, dan generator."""

import copy
import random
import unittest

from config import DATA_DIR
from core.generator import generate_instance
from core.problem import load_problem, parse_problem

DATA = DATA_DIR

VALID = {
    "ships": [{"id": "Deck-1", "width": 10, "length": 20, "max_capacity": 500}],
    "vehicles": [
        {"id": "A", "width": 3, "length": 4, "shipping_fee": 60, "weight": 5, "eta": 3},
        {"id": "B", "width": 1, "length": 2, "shipping_fee": 7.5, "weight": 0.5, "eta": 0},
    ],
}


def with_change(path: list, value):
    """Salinan VALID dengan satu field diganti (value=KeyError artinya field dihapus)."""
    data = copy.deepcopy(VALID)
    target = data
    for key in path[:-1]:
        target = target[key]
    if value is KeyError:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return data


class TestParseProblem(unittest.TestCase):
    def test_valid(self):
        problem = parse_problem(VALID, name="x")
        self.assertEqual(problem.name, "x")
        self.assertEqual([v.id for v in problem.vehicles], ["A", "B"])
        self.assertEqual(problem.vehicles[0].area, 12)
        self.assertEqual(problem.ships[0].area, 200)

    def test_extra_keys_ignored(self):
        data = with_change(["vehicles", 0, "type"], "sedan")
        data["meta"] = {"seed": 1}
        parse_problem(data)

    def test_invalid(self):
        cases = {
            "root bukan object": [],
            "ships kosong": with_change(["ships"], []),
            "vehicles hilang": with_change(["vehicles"], KeyError),
            "field wajib hilang": with_change(["vehicles", 0, "weight"], KeyError),
            "width nol": with_change(["vehicles", 0, "width"], 0),
            "width pecahan": with_change(["vehicles", 0, "width"], 2.5),
            "width bool": with_change(["vehicles", 0, "width"], True),
            "fee negatif": with_change(["vehicles", 0, "shipping_fee"], -1),
            "fee string": with_change(["vehicles", 0, "shipping_fee"], "60"),
            "berat nol": with_change(["vehicles", 0, "weight"], 0),
            "eta negatif": with_change(["vehicles", 0, "eta"], -1),
            "kapasitas nol": with_change(["ships", 0, "max_capacity"], 0),
            "id kosong": with_change(["vehicles", 0, "id"], " "),
            "id duplikat": with_change(["vehicles", 1, "id"], "A"),
        }
        for label, data in cases.items():
            with self.subTest(label), self.assertRaises(ValueError):
                parse_problem(data)


    def test_rejects_nonfinite_numeric_fields(self):
        for section, field in (("ships", "max_capacity"), ("vehicles", "weight"),
                               ("vehicles", "shipping_fee"), ("vehicles", "eta")):
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    parse_problem(with_change([section, 0, field], value))

class TestDataFiles(unittest.TestCase):
    def test_instances_load(self):
        for name in ("main", "small"):
            with self.subTest(name):
                problem = load_problem(DATA / f"{name}.json")
                self.assertEqual(problem.name, name)
                # instance harus "ketat": tidak semua kendaraan muat, dari sisi luas maupun berat
                ship = problem.ships[0]
                self.assertGreater(sum(v.area for v in problem.vehicles), ship.area)
                self.assertGreater(sum(v.weight for v in problem.vehicles), ship.max_capacity)


class TestGenerator(unittest.TestCase):
    def test_deterministic_and_valid(self):
        a = generate_instance(random.Random(7), 12, [(8, 10)])
        b = generate_instance(random.Random(7), 12, [(8, 10)])
        c = generate_instance(random.Random(8), 12, [(8, 10)])
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertEqual(len(parse_problem(a).vehicles), 12)

    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            generate_instance(random.Random(0), 3, [(4, 4)], types=["kapal selam"])


if __name__ == "__main__":
    unittest.main()
