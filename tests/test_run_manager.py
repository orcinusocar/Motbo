from pathlib import Path

from app.core.types import RunConfig, RunStatus
from app.runs.manager import RunManager


def test_run_completes_and_persists(tmp_path: Path, example_model: Path) -> None:
    config = RunConfig(duration=0.05, timestep=0.002, seed=0)
    with RunManager(data_dir=tmp_path, max_workers=1) as manager:
        record = manager.start(example_model, config)
        record = manager.wait(record.id, timeout=30)
        assert record.status == RunStatus.COMPLETED
        assert record.nstep > 0
        metrics = manager.metrics(record.id)
        assert metrics is not None
        assert metrics["nstep"] == record.nstep
        run_dir = Path(record.result_path)
        assert (run_dir / "config.yaml").exists()
        assert (run_dir / "metrics.json").exists()
        assert (run_dir / "simulation.log").exists()
        assert (run_dir / "trajectory.npz").exists()

    with RunManager(data_dir=tmp_path) as restored:
        loaded = restored.get(record.id)
        assert loaded.status == RunStatus.COMPLETED
        assert loaded.nstep == record.nstep


def test_cancel_run(tmp_path: Path, example_model: Path) -> None:
    config = RunConfig(duration=1000.0, timestep=0.002)
    with RunManager(data_dir=tmp_path, max_workers=1) as manager:
        record = manager.start(example_model, config)
        manager.cancel(record.id)
        record = manager.wait(record.id, timeout=30)
        assert record.status == RunStatus.CANCELLED


def test_invalid_model_fails_without_crash(tmp_path: Path) -> None:
    bad = tmp_path / "bad.xml"
    bad.write_text("<mujoco><broken>")
    with RunManager(data_dir=tmp_path, max_workers=1) as manager:
        first = manager.start(bad, RunConfig(duration=0.05))
        first = manager.wait(first.id, timeout=30)
        assert first.status == RunStatus.FAILED
        assert first.error_message

        good = tmp_path / "ok.xml"
        good.write_text((Path(__file__).resolve().parents[1] / "examples/models/simple_arm.xml").read_text())
        second = manager.start(good, RunConfig(duration=0.04, timestep=0.002, save_trajectory=False))
        second = manager.wait(second.id, timeout=30)
        assert second.status == RunStatus.COMPLETED
