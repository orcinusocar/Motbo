from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def dump_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def load_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


@dataclass
class RunConfig:
    duration: float = 1.0
    timestep: float | None = None
    seed: int = 0
    save_trajectory: bool = True
    render: bool = False

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError("duration 必须大于 0")
        if self.timestep is not None and self.timestep <= 0:
            raise ValueError("timestep 必须大于 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "duration": self.duration,
            "timestep": self.timestep,
            "seed": self.seed,
            "save_trajectory": self.save_trajectory,
            "render": self.render,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RunConfig:
        data = data or {}
        return cls(
            duration=float(data.get("duration", 1.0)),
            timestep=data.get("timestep"),
            seed=int(data.get("seed", 0)),
            save_trajectory=bool(data.get("save_trajectory", True)),
            render=bool(data.get("render", False)),
        )


@dataclass
class RunRecord:
    id: str
    status: RunStatus
    model_path: str
    config: RunConfig = field(default_factory=RunConfig)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration: float | None = None
    error_message: str | None = None
    result_path: str | None = None
    nstep: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "model_path": self.model_path,
            "config": self.config.to_dict(),
            "started_at": dump_dt(self.started_at),
            "finished_at": dump_dt(self.finished_at),
            "duration": self.duration,
            "error_message": self.error_message,
            "result_path": self.result_path,
            "nstep": self.nstep,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunRecord:
        return cls(
            id=str(data["id"]),
            status=RunStatus(data["status"]),
            model_path=str(data["model_path"]),
            config=RunConfig.from_dict(data.get("config")),
            started_at=load_dt(data.get("started_at")),
            finished_at=load_dt(data.get("finished_at")),
            duration=data.get("duration"),
            error_message=data.get("error_message"),
            result_path=data.get("result_path"),
            nstep=int(data.get("nstep", 0)),
        )
