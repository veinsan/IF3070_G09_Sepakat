"""Bounded observational snapshots for the local simulator, never search decisions.

The observer does not draw random numbers or mutate search states. Without an
observer, normal CLI/experiment runs do not allocate snapshots. Frames are actual
sampled configurations, not an interpolated path or a record of every transition.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from core.state import State

SearchObserver = Callable[[int, State, State, dict | None], None]


def _snapshot(state: State) -> dict:
    evaluation = state.evaluate()
    return {
        "positions": [list(p) if p is not None else None for p in state.positions],
        "objective": state.objective,
        "feasible": evaluation.is_feasible,
        "total_fee": evaluation.total_fee,
        "used_weight": list(evaluation.used_weight),
        "occupied_cells": list(evaluation.occupied_cells),
        "overlap_cells": evaluation.overlap_cells,
        "out_of_bound_cells": evaluation.out_of_bound_cells,
        "weight_units": evaluation.weight_units,
    }


class TraceRecorder:
    """Adaptively thin real states while retaining the initial and terminal frame.

    publish receives a detached list of frames at most five times a second, plus
    forced restart/terminal updates. Frame objects are never changed after capture.
    The worker transports these snapshots; it does not slow search to playback speed.
    """

    def __init__(self, max_frames: int = 240,
                 publish: Callable[[list[dict]], None] | None = None) -> None:
        if isinstance(max_frames, bool) or not isinstance(max_frames, int) or max_frames < 2:
            raise ValueError("max_frames harus integer >= 2")
        self.max_frames = max_frames
        self.publish = publish
        self.frames: list[dict] = []
        self.stride = 1
        self._last_publish = float("-inf")

    def __call__(self, step: int, current: State, best: State, details: dict | None = None) -> None:
        details = dict(details or {})
        force = step == 0 or details.get("event") in ("finished", "restart")
        if not force and step % self.stride:
            return
        same_step = bool(self.frames and self.frames[-1]["step"] == step)
        if same_step:
            details = {**self.frames[-1]["details"], **details}
        frame = {"step": step, "current": _snapshot(current), "best": _snapshot(best), "details": details}
        if same_step:
            self.frames[-1] = frame
        else:
            if len(self.frames) >= self.max_frames:
                self.frames = self.frames[::2]
                self.stride *= 2
            self.frames.append(frame)
        now = time.monotonic()
        if self.publish is not None and (force or now - self._last_publish >= 0.2):
            self.publish(list(self.frames))
            self._last_publish = now
