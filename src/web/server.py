"""Loopback-only workbench API with one isolated search process and in-memory history."""

from __future__ import annotations

import asyncio
import inspect
import io
import json
import math
import multiprocessing
import re
import threading
import time
import uuid
from collections import OrderedDict
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from queue import Empty
from typing import Any
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from config import DATA_DIR, GA_ELITISM
from core.objective import EPS
from core.problem import Problem, load_problem, parse_problem

LIMITS = {
    "max_body_bytes": 131072,
    "max_ships": 4,
    "max_vehicles": 80,
    "max_dimension": 128,
    "max_deck_cells": 1024,
    "max_total_capacity": 2000,
    "max_dp_cells": 250000,
    "max_dp_work": 20000000,
    "max_numeric_value": 1000000000,
    "max_label_length": 64,
    "max_iterations": 200000,
    "max_frames": 240,
    "history_size": 8,
    "timeout_s": 45,
    "min_seed": -2147483648,
    "max_seed": 2147483647,
}

ALGORITHM_INFO = {
    "steepest": ("Steepest Ascent", "Pilih neighbor terbaik dari seluruh kemungkinan. Berhenti saat tidak ada perbaikan."),
    "sideways": ("Sideways Move", "Izinkan langkah bernilai sama untuk melintasi plateau, dengan batas sideways."),
    "random_restart": ("Random Restart", "Ulangi pendakian dari state acak baru, lalu simpan hasil feasible terbaik."),
    "stochastic": ("Stochastic", "Uji satu neighbor acak per iterasi. Terima hanya jika nilainya membaik."),
    "sa": ("Simulated Annealing", "Terima penurunan dengan peluang exp(ΔE/T), lalu turunkan suhu secara geometris."),
    "ga": ("Genetic Algorithm", "Evolusikan populasi dengan roulette wheel, crossover satu titik, mutasi, dan elitism."),
}
PARAM_INFO = {
    "max_iterations": ("Batas iterasi", 0, 2000),
    "max_sideways": ("Maksimum sideways", 1, 1000),
    "max_restart": ("Maksimum restart", 0, 20),
    "max_no_improve": ("Batas tanpa perbaikan", 1, 100000),
    "iterations": ("Iterasi / generasi", 1, LIMITS["max_iterations"]),
    "population": ("Ukuran populasi", GA_ELITISM + 1, 200),
}
STATIC_DIR = Path(__file__).resolve().parent / "static"


def algorithm_metadata() -> list[dict[str, Any]]:
    from main import ALGORITHMS

    algorithms = []
    for key, (function, mapping) in ALGORITHMS.items():
        signature = inspect.signature(function)
        params = {}
        for option, argument in mapping.items():
            label, minimum, maximum = PARAM_INFO[option]
            if option == "max_iterations" and key == "stochastic":
                maximum = LIMITS["max_iterations"]
            if option == "iterations" and key == "ga":
                maximum = 2000
            default = min(signature.parameters[argument].default, maximum)
            params[option] = {"label": label, "default": default, "min": minimum,
                              "max": maximum, "step": 1}
        label, description = ALGORITHM_INFO[key]
        algorithms.append({"id": key, "label": label, "description": description, "params": params})
    return algorithms


def problem_json(problem: Problem) -> dict[str, Any]:
    return {"name": problem.name, "ships": [asdict(ship) for ship in problem.ships],
            "vehicles": [asdict(vehicle) for vehicle in problem.vehicles]}


def bounded_problem(raw: Any, name: str) -> Problem:
    """Run shared semantic validation, then bound every state/knapsack allocation dimension."""
    if not isinstance(raw, dict):
        raise ValueError("problem must be a JSON object")
    for key, maximum in (("ships", LIMITS["max_ships"]), ("vehicles", LIMITS["max_vehicles"])):
        items = raw.get(key)
        if isinstance(items, list) and len(items) > maximum:
            raise ValueError(f"Jumlah {key} melebihi batas {maximum}.")
    problem = parse_problem(raw, name=name)
    for item in (*problem.ships, *problem.vehicles):
        if len(item.id) > LIMITS["max_label_length"]:
            raise ValueError("Id kapal dan kendaraan maksimal 64 karakter.")
        if item.width > LIMITS["max_dimension"] or item.length > LIMITS["max_dimension"]:
            raise ValueError("Ukuran kapal atau kendaraan melebihi batas.")
    for vehicle in problem.vehicles:
        if any(value > LIMITS["max_numeric_value"] for value in
               (vehicle.weight, vehicle.shipping_fee, vehicle.eta)):
            raise ValueError("Nilai angka kendaraan melebihi batas.")
    area = sum(ship.area for ship in problem.ships)
    capacity = sum(ship.max_capacity for ship in problem.ships)
    if area > LIMITS["max_deck_cells"]:
        raise ValueError("Total luas geladak melebihi batas.")
    if capacity > LIMITS["max_total_capacity"]:
        raise ValueError("Total kapasitas kapal melebihi batas.")
    weight_cap = math.floor(sum(ship.max_capacity + EPS for ship in problem.ships))
    dp_cells = (area + 1) * (weight_cap + 1)
    if dp_cells > LIMITS["max_dp_cells"] or dp_cells * len(problem.vehicles) > LIMITS["max_dp_work"]:
        raise ValueError("Instance terlalu besar untuk dihitung batas atasnya di simulator.")
    return problem


def upload_label(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("problem.name must be a string")
    basename = value.replace("\\", "/").rsplit("/", 1)[-1]
    if basename.lower().endswith(".json"):
        basename = basename[:-5]
    label = re.sub(r"[^A-Za-z0-9_-]+", "_", basename).strip("_")
    return label[:LIMITS["max_label_length"]] or "uploaded"


def integer(value: Any, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def validate_run(body: Any, datasets: dict, algorithms: dict) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ValueError("request must be a JSON object")
    unknown = set(body) - {"algorithm", "dataset", "seed", "objective", "params", "problem"}
    if unknown:
        raise ValueError("unknown request fields: " + ", ".join(sorted(unknown)))
    algorithm = body.get("algorithm")
    dataset = body.get("dataset", "main")
    objective = body.get("objective", "fee")
    if not isinstance(algorithm, str) or algorithm not in algorithms:
        raise ValueError("unknown algorithm")
    if not isinstance(dataset, str) or dataset not in datasets:
        raise ValueError("unknown dataset")
    if objective not in ("fee", "eta"):
        raise ValueError("objective must be fee or eta")
    seed = integer(body.get("seed", 1), "seed", LIMITS["min_seed"], LIMITS["max_seed"])
    supplied = body.get("params", {})
    if not isinstance(supplied, dict):
        raise ValueError("params must be an object")
    metadata = algorithms[algorithm]["params"]
    unknown = set(supplied) - set(metadata)
    if unknown:
        raise ValueError("unknown algorithm parameters: " + ", ".join(sorted(unknown)))
    params = {key: integer(supplied.get(key, spec["default"]), key, spec["min"], spec["max"])
              for key, spec in metadata.items()}
    if "problem" in body:
        raw = body["problem"]
        name = upload_label(raw.get("name", "uploaded")) if isinstance(raw, dict) else "uploaded"
        problem = problem_json(bounded_problem(raw, name))
    else:
        problem = datasets[dataset]["problem"]
    return {"algorithm": algorithm, "dataset": dataset, "seed": seed,
            "objective": objective, "params": params, "problem": problem}


class JobManager:
    """One spawned worker, bounded terminal history, and a lifespan-owned monitor."""

    def __init__(self, *, timeout_s: float = LIMITS["timeout_s"], history_size: int = LIMITS["history_size"]):
        self.timeout_s = timeout_s
        self.history_size = history_size
        self.runs: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.active: str | None = None
        self.process = None
        self.events = None
        self.started = 0.0
        self.stopping = False
        self.lock = asyncio.Lock()
        self.plot_lock = threading.Lock()
        self.context = multiprocessing.get_context("spawn")

    def get(self, run_id: str) -> dict[str, Any]:
        if run_id not in self.runs:
            raise HTTPException(404, "Simulasi ini sudah tidak tersimpan di server. Muat ulang halaman atau jalankan kembali.")
        return self.runs[run_id]

    def prune(self) -> None:
        terminal = [key for key, run in self.runs.items() if run["status"] != "running"]
        for key in terminal[:-self.history_size]:
            del self.runs[key]

    async def start(self, spec: dict[str, Any]) -> dict[str, Any]:
        from web.worker import run_worker

        async with self.lock:
            if self.active is not None:
                raise HTTPException(409, "Masih ada simulasi yang berjalan. Tunggu sampai selesai atau batalkan dulu.")
            run_id = uuid.uuid4().hex
            params = spec["params"]
            target = params.get("iterations", params.get("max_iterations"))
            if spec["algorithm"] == "random_restart":
                target = target * (params["max_restart"] + 1) + params["max_restart"]
            run = {"id": run_id, "status": "running", "algorithm": spec["algorithm"],
                   "objective": spec["objective"], "seed": spec["seed"], "problem": spec["problem"],
                   "frames": [], "result": None, "error": None,
                   "progress": {"step": 0, "target": target}}
            events = self.context.Queue(maxsize=4)
            process = self.context.Process(target=run_worker, args=(spec, events, LIMITS["max_frames"]),
                                           name="cargo-search", daemon=True)
            try:
                process.start()
            except Exception:
                events.close()
                raise HTTPException(500, "Proses pencarian lokal gagal dimulai.") from None
            self.runs[run_id] = run
            self.active, self.process, self.events = run_id, process, events
            self.started = time.monotonic()
            self.prune()
            return {"id": run_id, "status": "running"}

    async def release(self) -> None:
        process, events = self.process, self.events
        if process is not None:
            def stop():
                process.join(timeout=0.1)
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=0.5)
                if process.is_alive():
                    process.kill()
                    process.join()
            await asyncio.to_thread(stop)
        if events is not None:
            events.close()
            events.cancel_join_thread()
        self.active = self.process = self.events = None
        self.prune()

    def drain(self, run: dict[str, Any]) -> None:
        while True:
            try:
                event = self.events.get_nowait()
            except Empty:
                return
            if "frames" in event:
                run["frames"] = event["frames"]
                if run["frames"]:
                    run["progress"]["step"] = run["frames"][-1]["step"]
            if event["kind"] == "completed":
                run["status"] = "completed"
                run["result"] = event["result"]
                run["progress"]["step"] = event["result"]["iterations"]
            elif event["kind"] == "failed":
                run["status"], run["error"] = "failed", event["error"]

    async def monitor(self) -> None:
        while not self.stopping:
            await asyncio.sleep(0.05)
            async with self.lock:
                if self.active is None:
                    continue
                run = self.runs[self.active]
                self.drain(run)
                if run["status"] == "running":
                    if time.monotonic() - self.started > self.timeout_s:
                        run["status"], run["error"] = "failed", "Pencarian melewati batas waktu 45 detik. Kecilkan iterasi atau populasi."
                    elif not self.process.is_alive():
                        self.drain(run)
                        if run["status"] == "running":
                            run["status"], run["error"] = "failed", "Proses pencarian berhenti tanpa hasil."
                if run["status"] != "running":
                    await self.release()

    async def cancel(self, run_id: str) -> dict[str, Any]:
        async with self.lock:
            run = self.get(run_id)
            if run["status"] == "running":
                self.drain(run)
                if run["status"] == "running":
                    run["status"] = "cancelled"
                await self.release()
            return run

    async def close(self) -> None:
        async with self.lock:
            if self.active is not None:
                self.runs[self.active]["status"] = "cancelled"
                await self.release()


def create_app(*, timeout_s: float = LIMITS["timeout_s"], history_size: int = LIMITS["history_size"]) -> FastAPI:
    datasets = {key: {"id": key, "label": label, "problem": problem_json(
        bounded_problem(problem_json(load_problem(DATA_DIR / f"{key}.json")), key))}
        for key, label in (("main", "Utama"), ("small", "Kecil (studi optimum eksak)"),
                           ("multi", "Armada multi-kapal"))}
    algorithms = {item["id"]: item for item in algorithm_metadata()}

    @asynccontextmanager
    async def lifespan(app):
        manager = JobManager(timeout_s=timeout_s, history_size=history_size)
        app.state.jobs = manager
        monitor = asyncio.create_task(manager.monitor())
        try:
            yield
        finally:
            manager.stopping = True
            try:
                await monitor
            finally:
                await manager.close()

    app = FastAPI(title="CARGO local workbench", lifespan=lifespan,
                  docs_url=None, redoc_url=None, openapi_url=None)

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        try:
            host = urlsplit("http://" + request.headers.get("host", "")).hostname
        except ValueError:
            host = None
        if host not in {"localhost", "127.0.0.1", "::1"}:
            return JSONResponse({"detail": "Only local hosts are accepted"}, status_code=400)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            origin = request.headers.get("origin")
            if origin is not None and origin != f"{request.url.scheme}://{request.headers.get('host', '')}":
                return JSONResponse({"detail": "Foreign Origin is not allowed"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/bootstrap")
    async def bootstrap():
        return {"datasets": list(datasets.values()), "algorithms": list(algorithms.values()),
                "limits": {**LIMITS, "timeout_s": timeout_s, "history_size": history_size}}

    @app.post("/api/runs", status_code=202)
    async def start_run(request: Request):
        if request.headers.get("content-type", "").split(";", 1)[0].strip() != "application/json":
            raise HTTPException(415, "Use application/json")
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError:
                raise HTTPException(400, "Invalid Content-Length") from None
            if length < 0:
                raise HTTPException(400, "Invalid Content-Length")
            if length > LIMITS["max_body_bytes"]:
                raise HTTPException(413, "Ukuran permintaan melebihi batas server.")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > LIMITS["max_body_bytes"]:
                raise HTTPException(413, "Ukuran permintaan melebihi batas server.")
            raw.extend(chunk)
        try:
            def reject_constant(value):
                raise ValueError("Non-finite JSON number: " + value)
            body = json.loads(raw, parse_constant=reject_constant)
            spec = validate_run(body, datasets, algorithms)
        except (ValueError, TypeError, RecursionError, OverflowError) as exc:
            raise HTTPException(422, str(exc)[:500]) from None
        return await request.app.state.jobs.start(spec)

    @app.get("/api/runs/{run_id}")
    async def get_run(run_id: str, request: Request):
        manager = request.app.state.jobs
        async with manager.lock:
            return {**manager.get(run_id), "retained_ids": list(manager.runs)}

    @app.post("/api/runs/{run_id}/cancel")
    async def cancel_run(run_id: str, request: Request):
        return await request.app.state.jobs.cancel(run_id)

    def completed(run_id: str, request: Request):
        run = request.app.state.jobs.get(run_id)
        if run["status"] != "completed":
            raise HTTPException(409, "Ekspor hanya tersedia untuk simulasi yang sudah selesai.")
        return run

    @app.get("/api/runs/{run_id}/download")
    async def download_run(run_id: str, request: Request):
        run = completed(run_id, request)
        return JSONResponse(run, headers={"Content-Disposition": f'attachment; filename="cargo-{run_id}.json"'})

    @app.get("/api/runs/{run_id}/plot.png")
    def plot_run_png(run_id: str, request: Request):
        from visualization.plots import plot_run

        run = completed(run_id, request)
        with request.app.state.jobs.plot_lock:
            figure = plot_run(run["result"])
            output = io.BytesIO()
            try:
                figure.savefig(output, format="png", dpi=120)
            finally:
                figure.clear()
        return Response(output.getvalue(), media_type="image/png",
                        headers={"Content-Disposition": f'attachment; filename="cargo-{run_id}.png"'})

    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    app.mount("/static", StaticFiles(directory=STATIC_DIR, check_dir=False), name="static")
    return app
