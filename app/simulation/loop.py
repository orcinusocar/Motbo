from __future__ import annotations

import time
from contextlib import nullcontext
from dataclasses import dataclass, field
from threading import Event
from typing import Any, Callable

import numpy as np

from app.core.types import RunStatus
from app.simulation.control import apply_default_control
from app.simulation.simulator import Simulator

ControlFn = Callable[[Any, Any], None]
StepFn = Callable[[Simulator], None]


@dataclass
class LoopBuffers:
    times: list[float] = field(default_factory=list)
    qpos: list[np.ndarray] = field(default_factory=list)
    qvel: list[np.ndarray] = field(default_factory=list)


@dataclass
class LoopResult:
    status: RunStatus
    buffers: LoopBuffers
    nstep: int


def run_loop(
    simulator: Simulator,
    duration: float,
    *,
    cancel: Event | None = None,
    save_trajectory: bool = True,
    apply_control: ControlFn = apply_default_control,
    viewer: Any | None = None,
    realtime: bool = False,
    on_step: StepFn | None = None,
) -> LoopResult:
    cancel = cancel or Event()
    buffers = LoopBuffers()
    nstep = 0

    while simulator.time < duration:
        if cancel.is_set() or _should_stop(viewer):
            return LoopResult(RunStatus.CANCELLED, buffers, nstep)
        if viewer is not None:
            viewer.before_step()
            if cancel.is_set() or _should_stop(viewer):
                return LoopResult(RunStatus.CANCELLED, buffers, nstep)

        step_start = time.perf_counter()
        with _guard(viewer):
            apply_control(simulator.model, simulator.data)
            simulator.step()
            nstep += 1
            if save_trajectory:
                buffers.times.append(float(simulator.time))
                buffers.qpos.append(np.array(simulator.data.qpos, copy=True))
                buffers.qvel.append(np.array(simulator.data.qvel, copy=True))
            if on_step is not None:
                on_step(simulator)
            if viewer is not None:
                viewer.after_step()

        if realtime:
            leftover = simulator.timestep - (time.perf_counter() - step_start)
            if leftover > 0:
                time.sleep(leftover)

    return LoopResult(RunStatus.COMPLETED, buffers, nstep)


def _should_stop(viewer: Any | None) -> bool:
    return bool(viewer is not None and viewer.should_stop())


def _guard(viewer: Any | None):
    if viewer is None:
        return nullcontext()
    return viewer.guard()
