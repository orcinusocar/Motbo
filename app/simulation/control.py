from __future__ import annotations

import numpy as np


def apply_default_control(model, data) -> None:
    if model.nu < 2:
        return
    t = float(data.time)
    data.ctrl[0] = 0.55 * np.sin(2 * np.pi * 0.35 * t)
    data.ctrl[1] = -0.8 + 0.65 * np.sin(2 * np.pi * 0.5 * t + 0.4)
