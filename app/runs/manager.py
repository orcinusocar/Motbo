from __future__ import annotations

import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

import numpy as np

from app.core.config import DEFAULT_DATA_DIR
from app.core.paths import PathGuardError, validate_run_id
from app.core.types import RunConfig, RunRecord, RunStatus, utcnow
from app.metrics.collector import MetricsCollector
from app.simulation.loop import run_loop
from app.simulation.simulator import Simulator
from app.simulation.viewer import default_viewer_factory
from app.storage.run_store import RunStore

ViewerFactory = Callable[..., object]


class RunNotFound(KeyError):
    pass


class RunManager:
    def __init__(
        self,
        data_dir: str | Path | None = None,
        max_workers: int = 2,
        viewer_factory: ViewerFactory | None = None,
    ):
        self.data_dir = Path(data_dir or DEFAULT_DATA_DIR).resolve()
        self.store = RunStore(self.data_dir)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="motbo-run")
        self._lock = threading.Lock()
        self._records: dict[str, RunRecord] = {}
        self._cancels: dict[str, threading.Event] = {}
        self._done: dict[str, threading.Event] = {}
        self._viewers: dict[str, object] = {}
        self._viewer_factory = viewer_factory or default_viewer_factory
        self._load_persisted()

    def start(self, model_path: str | Path, config: RunConfig | None = None) -> RunRecord:
        config = config or RunConfig()
        run_id = uuid.uuid4().hex
        result_path = str(self.store.create(run_id))
        record = RunRecord(
            id=run_id,
            status=RunStatus.PENDING,
            model_path=str(Path(model_path).resolve()),
            config=config,
            result_path=result_path,
        )
        cancel = threading.Event()
        done = threading.Event()
        with self._lock:
            self._records[run_id] = record
            self._cancels[run_id] = cancel
            self._done[run_id] = done
        self.store.write_config(
            run_id,
            {
                "run_id": run_id,
                "model_path": record.model_path,
                "config": config.to_dict(),
            },
        )
        self.store.write_record(record)
        self.store.append_log(run_id, "run created")
        if config.render:
            self._execute(run_id)
        else:
            self._executor.submit(self._execute, run_id)
        return self.get(run_id)

    def get(self, run_id: str) -> RunRecord:
        try:
            validate_run_id(run_id)
        except PathGuardError as exc:
            raise RunNotFound(str(exc)) from exc
        with self._lock:
            record = self._records.get(run_id)
            if record is not None:
                return self._copy_record(record)
        loaded = self.store.load_record(run_id)
        if loaded is None:
            raise RunNotFound(f"运行不存在: {run_id}")
        with self._lock:
            self._records[run_id] = loaded
        return self._copy_record(loaded)

    def list_runs(self) -> list[RunRecord]:
        with self._lock:
            ids = list(self._records)
        return [self.get(run_id) for run_id in sorted(ids)]

    def metrics(self, run_id: str) -> dict | None:
        self.get(run_id)
        return self.store.load_metrics(run_id)

    def viewer(self, run_id: str) -> object | None:
        with self._lock:
            return self._viewers.get(run_id)

    def cancel(self, run_id: str) -> RunRecord:
        record = self.get(run_id)
        if record.status in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}:
            return record
        with self._lock:
            event = self._cancels.get(run_id)
        if event is not None:
            event.set()
            self.store.append_log(run_id, "cancel requested")
        return self.get(run_id)

    def wait(self, run_id: str, timeout: float | None = None) -> RunRecord:
        with self._lock:
            done = self._done.get(run_id)
        if done is None:
            return self.get(run_id)
        if not done.wait(timeout):
            raise TimeoutError(f"等待运行超时: {run_id}")
        return self.get(run_id)

    def close(self) -> None:
        self._executor.shutdown(wait=True)

    def __enter__(self) -> RunManager:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _load_persisted(self) -> None:
        for run_id in self.store.list_run_ids():
            record = self.store.load_record(run_id)
            if record is None:
                continue
            with self._lock:
                self._records[run_id] = record

    def _execute(self, run_id: str) -> None:
        try:
            self._run_simulation(run_id)
        except Exception as exc:
            self._finish(run_id, RunStatus.FAILED, error_message=str(exc))
        finally:
            with self._lock:
                done = self._done.get(run_id)
            if done is not None:
                done.set()

    def _run_simulation(self, run_id: str) -> None:
        record = self.get(run_id)
        cancel = self._cancels[run_id]
        self._update(run_id, status=RunStatus.RUNNING, started_at=utcnow())
        self.store.append_log(run_id, f"loading model {record.model_path}")

        simulator = Simulator(record.model_path, timestep=record.config.timestep)
        simulator.reset(seed=record.config.seed)
        collector = MetricsCollector()
        viewer = None
        if record.config.render:
            viewer = self._viewer_factory(
                simulator.model,
                simulator.data,
                record.model_path,
                run_id,
            )
            with self._lock:
                self._viewers[run_id] = viewer
            self.store.append_log(run_id, "viewer attached to run MjData")

        collector.start()
        self.store.append_log(
            run_id,
            f"simulation started duration={record.config.duration} timestep={simulator.timestep} render={record.config.render}",
        )

        def physics() -> None:
            result = run_loop(
                simulator,
                record.config.duration,
                cancel=cancel,
                save_trajectory=record.config.save_trajectory,
                viewer=viewer,
                realtime=bool(getattr(viewer, "realtime", False)),
                on_step=lambda _sim: collector.on_step(),
            )
            metrics = collector.snapshot(simulator.time, simulator.timestep)
            self._save_outputs(
                run_id,
                metrics,
                record.config.save_trajectory,
                result.buffers.times,
                result.buffers.qpos,
                result.buffers.qvel,
            )
            self._finish(
                run_id,
                result.status,
                duration=metrics["duration"],
                nstep=metrics["nstep"],
            )

        if viewer is not None:
            viewer.run(physics)
        else:
            physics()

    def _save_outputs(
        self,
        run_id: str,
        metrics: dict,
        save_traj: bool,
        times: list[float],
        qpos: list[np.ndarray],
        qvel: list[np.ndarray],
    ) -> None:
        self.store.write_metrics(run_id, metrics)
        if save_traj and times:
            self.store.write_trajectory(
                run_id,
                time=np.asarray(times, dtype=np.float64),
                qpos=np.vstack(qpos),
                qvel=np.vstack(qvel),
            )
        self.store.append_log(
            run_id,
            f"metrics nstep={metrics['nstep']} duration={metrics['duration']:.4f} fps={metrics['fps']:.2f}",
        )

    def _finish(
        self,
        run_id: str,
        status: RunStatus,
        error_message: str | None = None,
        duration: float | None = None,
        nstep: int | None = None,
    ) -> None:
        updates = {
            "status": status,
            "finished_at": utcnow(),
            "error_message": error_message,
        }
        if duration is not None:
            updates["duration"] = duration
        if nstep is not None:
            updates["nstep"] = nstep
        self._update(run_id, **updates)
        if error_message:
            self.store.append_log(run_id, f"failed: {error_message}")
        else:
            self.store.append_log(run_id, f"finished status={status.value}")

    def _update(self, run_id: str, **kwargs) -> None:
        with self._lock:
            record = self._records[run_id]
            for key, value in kwargs.items():
                setattr(record, key, value)
            snapshot = self._copy_record(record)
        self.store.write_record(snapshot)

    @staticmethod
    def _copy_record(record: RunRecord) -> RunRecord:
        return RunRecord.from_dict(record.to_dict())
