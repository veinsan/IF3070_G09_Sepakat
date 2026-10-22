"""Real local-worker API boundaries, lifecycle, and result/trace consistency."""

import copy
import time
import unittest

from fastapi.testclient import TestClient

from core.eta_objective import eta_problem
from core.problem import parse_problem
from core.state import State
from search.result import RunResult
from web.server import LIMITS, create_app


class TestWebApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.context = TestClient(self.app, base_url="http://127.0.0.1")
        self.client = self.context.__enter__()
        self.bootstrap = self.client.get("/api/bootstrap").json()

    def tearDown(self):
        self.context.__exit__(None, None, None)

    def request(self, **overrides):
        body = {"algorithm": "sa", "dataset": "small", "seed": 4,
                "objective": "fee", "params": {"iterations": 8}}
        body.update(overrides)
        return body

    def wait_terminal(self, run_id):
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            response = self.client.get(f"/api/runs/{run_id}")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            if data["status"] != "running":
                return data
            time.sleep(0.03)
        self.fail("worker did not reach a terminal status")


    def test_real_run_frames_result_and_exports_agree(self):
        for objective in ("fee", "eta"):
            with self.subTest(objective=objective):
                response = self.client.post("/api/runs", json=self.request(objective=objective))
                self.assertEqual(response.status_code, 202, response.text)
                run_id = response.json()["id"]
                data = self.wait_terminal(run_id)
                self.assertEqual(data["status"], "completed", data["error"])
                original = parse_problem(data["problem"], name=data["problem"]["name"])
                problem = eta_problem(original) if objective == "eta" else original
                result = RunResult.from_dict(problem, data["result"])
                self.assertEqual(data["result"], result.to_dict())
                self.assertEqual(data["frames"][0]["step"], 0)
                self.assertEqual(data["frames"][-1]["step"], result.iterations)
                self.assertEqual(data["progress"]["step"], result.iterations)
                self.assertLessEqual(len(data["frames"]), LIMITS["max_frames"])
                for frame in data["frames"]:
                    for key in ("current", "best"):
                        view = frame[key]
                        positions = [tuple(p) if p is not None else None for p in view["positions"]]
                        state = State(problem, positions)
                        self.assertAlmostEqual(view["objective"], state.objective)
                        self.assertEqual(view["feasible"], state.is_feasible)
                    self.assertTrue(frame["best"]["feasible"])
                self.assertAlmostEqual(data["frames"][-1]["best"]["objective"],
                                       data["result"]["final_objective"])
                download = self.client.get(f"/api/runs/{run_id}/download")
                self.assertEqual(download.status_code, 200)
                self.assertEqual(download.json()["result"], data["result"])
                self.assertEqual(download.json()["frames"], data["frames"])
                image = self.client.get(f"/api/runs/{run_id}/plot.png")
                self.assertEqual(image.status_code, 200)
                self.assertEqual(image.content[:8], b"\x89PNG\r\n\x1a\n")
                cancelled = self.client.post(f"/api/runs/{run_id}/cancel")
                self.assertEqual(cancelled.json()["status"], "completed")
                self.assertEqual(cancelled.json()["result"], data["result"])

    def test_algorithm_semantic_limits_reject_before_starting_worker(self):
        for algorithm, params in (
            ("ga", {"population": 2, "iterations": 1}),
            ("sideways", {"max_sideways": 0}),
            ("stochastic", {"max_no_improve": 0}),
        ):
            with self.subTest(algorithm=algorithm):
                response = self.client.post("/api/runs", json=self.request(algorithm=algorithm, params=params))
                try:
                    self.assertEqual(response.status_code, 422)
                    self.assertIsNone(self.app.state.jobs.active)
                finally:
                    if response.status_code == 202:
                        self.client.post(f"/api/runs/{response.json()['id']}/cancel")

    def test_invalid_boundaries_do_not_start_a_worker(self):
        small = copy.deepcopy(self.bootstrap["datasets"][1]["problem"])
        malformed = copy.deepcopy(small)
        malformed["vehicles"][0]["weight"] = True
        huge_grid = copy.deepcopy(small)
        huge_grid["ships"][0]["width"] = 10**9
        huge_dp = copy.deepcopy(small)
        huge_dp["ships"][0]["max_capacity"] = 10**9
        dp_budget = copy.deepcopy(small)
        dp_budget["ships"][0].update(width=32, length=32, max_capacity=2000)
        oversized_list = copy.deepcopy(small)
        oversized_list["vehicles"] *= LIMITS["max_vehicles"] + 1
        bad_cases = [
            self.request(algorithm="unknown"), self.request(dataset="../../etc/passwd"),
            self.request(params={"population": 10}), self.request(params={"iterations": True}),
            self.request(params={"iterations": 2.5}), self.request(params={"iterations": "5"}),
            self.request(params={"iterations": LIMITS["max_iterations"] + 1}),
            self.request(seed=True), self.request(objective="other"),
            self.request(problem=malformed), self.request(problem=huge_grid),
            self.request(problem=huge_dp), self.request(problem=dp_budget),
            self.request(problem=oversized_list), self.request(problem=[]),
        ]
        for body in bad_cases:
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/api/runs", json=body).status_code, 422)
                self.assertIsNone(self.app.state.jobs.active)
        response = self.client.post("/api/runs", content=b" " * (LIMITS["max_body_bytes"] + 1),
                                    headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(self.client.post("/api/runs", content='{"seed":NaN}',
                                         headers={"Content-Type": "application/json"}).status_code, 422)
        self.assertEqual(self.client.post("/api/runs", content="{",
                                         headers={"Content-Type": "application/json"}).status_code, 422)

    def test_upload_name_is_a_label_and_original_fees_are_preserved(self):
        problem = copy.deepcopy(self.bootstrap["datasets"][1]["problem"])
        problem["name"] = "../../unsafe/path.json"
        response = self.client.post("/api/runs", json=self.request(problem=problem, objective="eta"))
        self.assertEqual(response.status_code, 202)
        data = self.wait_terminal(response.json()["id"])
        self.assertEqual(data["status"], "completed", data["error"])
        self.assertNotIn("/", data["problem"]["name"])
        self.assertNotIn("..", data["problem"]["name"])
        self.assertEqual(data["problem"]["vehicles"], problem["vehicles"])
        self.assertEqual(data["result"]["extra"]["objective"], "eta")

    def test_cancel_conflict_missing_and_shutdown_cleanup(self):
        body = self.request(dataset="main", algorithm="ga",
                            params={"population": 200, "iterations": 2000})
        response = self.client.post("/api/runs", json=body)
        self.assertEqual(response.status_code, 202)
        run_id = response.json()["id"]
        process = self.app.state.jobs.process
        self.assertEqual(self.client.post("/api/runs", json=body).status_code, 409)
        self.assertEqual(self.client.get(f"/api/runs/{run_id}/download").status_code, 409)
        self.assertEqual(self.client.get("/api/bootstrap").status_code, 200)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            progress = self.client.get(f"/api/runs/{run_id}").json()
            if progress["progress"]["step"] > 0 or progress["status"] != "running":
                break
            time.sleep(0.03)
        self.assertEqual(progress["status"], "running")
        self.assertGreater(progress["progress"]["step"], 0)
        self.assertEqual(progress["progress"]["step"], progress["frames"][-1]["step"])
        response = self.client.post(f"/api/runs/{run_id}/cancel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "cancelled")
        self.assertFalse(process.is_alive())
        self.assertIsNone(self.app.state.jobs.active)
        for suffix in ("", "/download", "/plot.png"):
            self.assertEqual(self.client.get("/api/runs/missing" + suffix).status_code, 404)
        self.assertEqual(self.client.post("/api/runs/missing/cancel").status_code, 404)
        response = self.client.post("/api/runs", json=body)
        self.assertEqual(response.status_code, 202)
        process = self.app.state.jobs.process
        self.context.__exit__(None, None, None)
        self.assertFalse(process.is_alive())
        self.context = TestClient(self.app, base_url="http://127.0.0.1")
        self.client = self.context.__enter__()

    def test_foreign_origins_and_hosts_cannot_mutate(self):
        body = self.request()
        for origin in ("https://evil.example", "null", "http://localhost.evil:8000"):
            response = self.client.post("/api/runs", json=body, headers={"Origin": origin})
            self.assertEqual(response.status_code, 403)
        response = self.client.post("/api/runs", json=body,
                                    headers={"Host": "evil.example", "Origin": "http://evil.example"})
        self.assertEqual(response.status_code, 400)
        response = self.client.post("/api/runs", json=body, headers={"Origin": "http://127.0.0.1"})
        self.assertEqual(response.status_code, 202)
        run_id = response.json()["id"]
        response = self.client.post(f"/api/runs/{run_id}/cancel", headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        self.client.post(f"/api/runs/{run_id}/cancel")

    def test_wall_timeout_stops_worker_and_releases_slot(self):
        app = create_app(timeout_s=0.001)
        with TestClient(app, base_url="http://127.0.0.1") as client:
            response = client.post("/api/runs", json=self.request(
                algorithm="ga", dataset="main", params={"population": 200, "iterations": 2000}))
            self.assertEqual(response.status_code, 202)
            run_id = response.json()["id"]
            process = app.state.jobs.process
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                data = client.get(f"/api/runs/{run_id}").json()
                if data["status"] != "running":
                    break
                time.sleep(0.02)
            self.assertEqual(data["status"], "failed")
            self.assertIsNotNone(data["error"])
            self.assertIsNone(data["result"])
            self.assertFalse(process.is_alive())
            self.assertIsNone(app.state.jobs.active)

    def test_completed_history_evicts_oldest_without_losing_recent_result(self):
        app = create_app(history_size=2)
        with TestClient(app, base_url="http://127.0.0.1") as client:
            ids = []
            for seed in (1, 2, 3):
                response = client.post("/api/runs", json=self.request(seed=seed))
                self.assertEqual(response.status_code, 202)
                run_id = response.json()["id"]
                ids.append(run_id)
                deadline = time.monotonic() + 25
                while time.monotonic() < deadline:
                    data = client.get(f"/api/runs/{run_id}").json()
                    if data["status"] != "running":
                        break
                    time.sleep(0.03)
                self.assertEqual(data["status"], "completed", data.get("error"))
            self.assertEqual(client.get(f"/api/runs/{ids[0]}").status_code, 404)
            for run_id in ids[1:]:
                data = client.get(f"/api/runs/{run_id}").json()
                self.assertEqual(data["status"], "completed")
                self.assertIsNotNone(data["result"])
                self.assertNotIn(ids[0], data.get("retained_ids", []))
                self.assertIn(run_id, data.get("retained_ids", []))
            self.assertEqual(len(app.state.jobs.runs), 2)


if __name__ == "__main__":
    unittest.main()
