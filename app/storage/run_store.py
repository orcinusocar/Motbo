from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from app.core.paths import ensure_within, validate_run_id
from app.core.types import RunRecord


class RunStore:
    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir).resolve()
        self.runs_dir = self.data_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        validate_run_id(run_id)
        return ensure_within(self.runs_dir / run_id, self.runs_dir)

    def create(self, run_id: str) -> Path:
        path = self.run_dir(run_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_config(self, run_id: str, payload: dict[str, Any]) -> Path:
        path = self.run_dir(run_id) / "config.yaml"
        self._atomic_write(path, yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
        return path

    def write_record(self, record: RunRecord) -> Path:
        path = self.run_dir(record.id) / "status.json"
        self._atomic_write(path, json.dumps(record.to_dict(), indent=2, ensure_ascii=False))
        return path

    def write_metrics(self, run_id: str, metrics: dict[str, Any]) -> Path:
        path = self.run_dir(run_id) / "metrics.json"
        self._atomic_write(path, json.dumps(metrics, indent=2, ensure_ascii=False))
        return path

    def write_trajectory(self, run_id: str, **arrays: np.ndarray) -> Path:
        path = self.run_dir(run_id) / "trajectory.npz"
        np.savez_compressed(path, **arrays)
        return path

    def append_log(self, run_id: str, message: str) -> None:
        path = self.run_dir(run_id) / "simulation.log"
        stamp = datetime.now(timezone.utc).isoformat()
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{stamp} {message}\n")

    def load_record(self, run_id: str) -> RunRecord | None:
        path = self.run_dir(run_id) / "status.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return RunRecord.from_dict(data)

    def load_metrics(self, run_id: str) -> dict[str, Any] | None:
        path = self.run_dir(run_id) / "metrics.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_run_ids(self) -> list[str]:
        ids: list[str] = []
        for child in self.runs_dir.iterdir():
            if child.is_dir() and (child / "status.json").exists():
                ids.append(child.name)
        return sorted(ids)

    @staticmethod
    def _atomic_write(path: Path, text: str) -> None:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
