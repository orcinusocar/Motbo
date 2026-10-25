from pathlib import Path
from threading import Event

import numpy as np

from app.core.types import RunStatus
from app.simulation.control import apply_default_control
from app.simulation.loop import run_loop
from app.simulation.simulator import Simulator
from app.simulation.viewer import FakeViewer


def test_control_writes_same_mjdata(example_model: Path) -> None:
    sim = Simulator(example_model)
    sim.reset(seed=0)
    data_id = id(sim.data)
    apply_default_control(sim.model, sim.data)
    assert id(sim.data) == data_id
    assert sim.model.nu >= 2
    assert float(np.linalg.norm(sim.data.ctrl)) > 0


def test_loop_keeps_single_mjdata(example_model: Path) -> None:
    sim = Simulator(example_model, timestep=0.002)
    sim.reset(seed=0)
    data_id = id(sim.data)
    result = run_loop(sim, duration=0.04, save_trajectory=True)
    assert result.status == RunStatus.COMPLETED
    assert result.nstep > 0
    assert id(sim.data) == data_id
    assert result.buffers.qpos
    np.testing.assert_allclose(result.buffers.qpos[-1], sim.data.qpos)


def test_loop_viewer_sees_same_data(example_model: Path) -> None:
    sim = Simulator(example_model, timestep=0.002)
    sim.reset(seed=1)
    viewer = FakeViewer(sim.model, sim.data)
    result = run_loop(sim, duration=0.04, viewer=viewer)
    assert result.status == RunStatus.COMPLETED
    assert viewer.frames
    assert {frame["data_id"] for frame in viewer.frames} == {id(sim.data)}
    np.testing.assert_allclose(viewer.frames[-1]["qpos"], sim.data.qpos)
    np.testing.assert_allclose(viewer.frames[-1]["ctrl"], sim.data.ctrl)


def test_loop_cancel(example_model: Path) -> None:
    sim = Simulator(example_model, timestep=0.002)
    sim.reset(seed=0)
    cancel = Event()
    cancel.set()
    result = run_loop(sim, duration=1.0, cancel=cancel)
    assert result.status == RunStatus.CANCELLED
    assert result.nstep == 0
