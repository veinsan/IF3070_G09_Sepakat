"""Spawn-safe CPU worker. Only immutable input and bounded trace events cross IPC."""

from queue import Full
from typing import Any

from core.eta_objective import run_eta
from core.problem import parse_problem
from main import ALGORITHMS
from search.trace import TraceRecorder


def run_worker(spec: dict[str, Any], events, max_frames: int) -> None:
    def publish(frames):
        try:
            events.put_nowait({"kind": "progress", "frames": list(frames)})
        except Full:
            pass

    try:
        problem = parse_problem(spec["problem"], name=spec["problem"]["name"])
        recorder = TraceRecorder(max_frames=max_frames, publish=publish)
        function, mapping = ALGORITHMS[spec["algorithm"]]
        params = {mapping[key]: value for key, value in spec["params"].items()}
        params["observer"] = recorder
        run = (run_eta(function, problem, seed=spec["seed"], **params)
               if spec["objective"] == "eta"
               else function(problem, seed=spec["seed"], **params))
        events.put({"kind": "completed", "frames": recorder.frames, "result": run.to_dict()})
    except Exception as exc:
        events.put({"kind": "failed", "error": f"{type(exc).__name__}: {exc}"[:500]})
    finally:
        events.close()
        events.join_thread()
