from __future__ import annotations

from pathlib import Path

import mujoco
import numpy as np

from app.models.loader import load_mj_model


class Simulator:
    def __init__(self, model_path: str | Path, timestep: float | None = None):
        self.model_path = Path(model_path).resolve()
        self.model = load_mj_model(self.model_path)
        if timestep is not None:
            self.model.opt.timestep = timestep
        self.data = mujoco.MjData(self.model)

    @property
    def timestep(self) -> float:
        return float(self.model.opt.timestep)

    @property
    def time(self) -> float:
        return float(self.data.time)

    def reset(self, seed: int = 0) -> None:
        mujoco.mj_resetData(self.model, self.data)
        rng = np.random.default_rng(seed)
        self.data.qpos[:] = self.model.qpos0
        if self.model.nq > 0:
            self.data.qpos[:] += rng.normal(0.0, 1e-4, size=self.model.nq)
        mujoco.mj_forward(self.model, self.data)

    def step(self) -> None:
        mujoco.mj_step(self.model, self.data)

    def snapshot(self) -> dict[str, np.ndarray]:
        return {
            "time": np.array(self.data.time, dtype=np.float64),
            "qpos": np.array(self.data.qpos, dtype=np.float64, copy=True),
            "qvel": np.array(self.data.qvel, dtype=np.float64, copy=True),
        }
