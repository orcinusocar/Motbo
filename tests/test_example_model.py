from pathlib import Path

import mujoco
import numpy as np

from app.models.loader import load_mj_model


def test_example_model_is_visible_above_floor(example_model: Path) -> None:
    model = load_mj_model(example_model)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)

    assert model.ngeom >= 6
    assert model.njnt >= 2
    assert model.nu >= 2
    assert model.ncam >= 1
    assert model.stat.center[2] > 0

    plane = int(mujoco.mjtGeom.mjGEOM_PLANE)
    zs = [float(data.geom_xpos[i][2]) for i in range(model.ngeom) if int(model.geom_type[i]) != plane]
    assert zs
    assert min(zs) >= -1e-6


def test_example_model_actuators_move_joints(example_model: Path) -> None:
    model = load_mj_model(example_model)
    data = mujoco.MjData(model)
    data.ctrl[:] = [0.6, -1.0]
    for _ in range(400):
        mujoco.mj_step(model, data)
    assert np.linalg.norm(data.qpos) > 0.2
