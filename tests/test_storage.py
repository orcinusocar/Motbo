from pathlib import Path

import pytest

from app.core.paths import PathGuardError
from app.core.types import RunConfig, RunRecord, RunStatus
from app.storage.run_store import RunStore


def test_write_and_load_record(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    run_id = "a" * 32
    store.create(run_id)
    record = RunRecord(
        id=run_id,
        status=RunStatus.COMPLETED,
        model_path="/tmp/model.xml",
        config=RunConfig(duration=0.1),
        nstep=10,
        result_path=str(store.run_dir(run_id)),
    )
    store.write_record(record)
    store.write_metrics(run_id, {"nstep": 10, "fps": 100.0})
    loaded = store.load_record(run_id)
    assert loaded is not None
    assert loaded.status == RunStatus.COMPLETED
    assert store.load_metrics(run_id)["nstep"] == 10


def test_reject_invalid_run_id(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    with pytest.raises(PathGuardError):
        store.run_dir("../secret")
