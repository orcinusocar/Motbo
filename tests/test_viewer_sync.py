from pathlib import Path

import numpy as np

from app.core.types import RunConfig, RunStatus
from app.runs.manager import RunManager
from app.simulation.viewer import FakeViewer


def test_render_run_shares_mjdata_and_persists(tmp_path: Path, example_model: Path) -> None:
    captured: dict[str, FakeViewer] = {}

    def factory(model, data, model_path: str = "", run_id: str = "") -> FakeViewer:
        viewer = FakeViewer(model, data, model_path, run_id)
        captured["viewer"] = viewer
        return viewer

    config = RunConfig(duration=0.05, timestep=0.002, seed=0, render=True)
    with RunManager(data_dir=tmp_path, max_workers=1, viewer_factory=factory) as manager:
        record = manager.start(example_model, config)
        record = manager.wait(record.id, timeout=10)
        assert record.status == RunStatus.COMPLETED
        assert record.config.render
        viewer = captured["viewer"]
        assert manager.viewer(record.id) is viewer
        assert viewer.frames
        assert {frame["data_id"] for frame in viewer.frames} == {id(viewer.data)}
        assert viewer.data is not None
        assert viewer.model is not None
        metrics = manager.metrics(record.id)
        assert metrics is not None
        assert metrics["nstep"] == record.nstep == len(viewer.frames)
        run_dir = Path(record.result_path)
        traj = np.load(run_dir / "trajectory.npz")
        np.testing.assert_allclose(traj["qpos"][-1], viewer.frames[-1]["qpos"])
        np.testing.assert_allclose(traj["qpos"][-1], viewer.data.qpos)
        assert (run_dir / "status.json").exists()
        assert (run_dir / "metrics.json").exists()
        assert (run_dir / "simulation.log").exists()
        log = (run_dir / "simulation.log").read_text()
        assert "viewer attached to run MjData" in log


def test_headless_does_not_create_viewer(tmp_path: Path, example_model: Path) -> None:
    calls = {"n": 0}

    def factory(*_args, **_kwargs) -> FakeViewer:
        calls["n"] += 1
        raise AssertionError("headless 不应创建 Viewer")

    config = RunConfig(duration=0.04, timestep=0.002, render=False)
    with RunManager(data_dir=tmp_path, viewer_factory=factory) as manager:
        record = manager.start(example_model, config)
        record = manager.wait(record.id, timeout=10)
        assert record.status == RunStatus.COMPLETED
        assert calls["n"] == 0
        assert manager.viewer(record.id) is None
