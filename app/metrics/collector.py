from __future__ import annotations

import time
from typing import Any


class MetricsCollector:
    def __init__(self) -> None:
        self.nstep = 0
        self._started_at: float | None = None

    def start(self) -> None:
        self.nstep = 0
        self._started_at = time.perf_counter()

    def on_step(self) -> None:
        self.nstep += 1

    def snapshot(self, sim_time: float, timestep: float) -> dict[str, Any]:
        elapsed = 0.0
        if self._started_at is not None:
            elapsed = time.perf_counter() - self._started_at
        fps = self.nstep / elapsed if elapsed > 0 else 0.0
        return {
            "nstep": self.nstep,
            "sim_time": sim_time,
            "timestep": timestep,
            "duration": elapsed,
            "fps": fps,
        }
