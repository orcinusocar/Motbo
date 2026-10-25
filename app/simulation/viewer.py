from __future__ import annotations

import threading
import time
from contextlib import nullcontext
from typing import Any, Callable

import mujoco
import numpy as np


class FakeViewer:
    realtime = False

    def __init__(self, model, data, model_path: str = "", run_id: str = ""):
        self.model = model
        self.data = data
        self.model_path = model_path
        self.run_id = run_id
        self.frames: list[dict[str, Any]] = []
        self.closed = False

    def run(self, physics: Callable[[], None]) -> None:
        physics()

    def guard(self):
        return nullcontext()

    def before_step(self) -> None:
        return None

    def after_step(self) -> None:
        self.frames.append(
            {
                "data_id": id(self.data),
                "time": float(self.data.time),
                "qpos": np.array(self.data.qpos, copy=True),
                "ctrl": np.array(self.data.ctrl, copy=True),
            }
        )

    def should_stop(self) -> bool:
        return self.closed

    def close(self) -> None:
        self.closed = True


def bind_glfw() -> None:
    import glfw
    from mujoco import _simulate

    if not glfw._glfw:
        raise RuntimeError("GLFW dynamic library handle is not available")
    _simulate.set_glfw_dlhandle(glfw._glfw._handle)


class SimulateViewer:
    realtime = True

    def __init__(self, model, data, model_path: str = "", run_id: str = ""):
        self.model = model
        self.data = data
        self.model_path = model_path
        self.run_id = run_id
        self._simulate = None

    def run(self, physics: Callable[[], None]) -> None:
        import glfw
        from mujoco import _simulate

        bind_glfw()

        cam = mujoco.MjvCamera()
        mujoco.mjv_defaultCamera(cam)
        cam.lookat[:] = self.model.stat.center
        cam.distance = max(self.model.stat.extent * 1.5, 0.6)
        cam.azimuth = 135
        cam.elevation = -20
        opt = mujoco.MjvOption()
        pert = mujoco.MjvPerturb()
        simulate = _simulate.Simulate(cam, opt, pert, None, True, None)
        self._simulate = simulate
        caption = self.model_path
        if self.run_id:
            caption = f"{self.model_path} [{self.run_id[:8]}]"

        if not glfw.init():
            raise RuntimeError("无法初始化 GLFW")

        error: list[BaseException] = []

        def worker() -> None:
            try:
                simulate.load_message(caption)
                simulate.load(self.model, self.data, caption)
                simulate.load_message_clear()
                physics()
            except BaseException as exc:
                error.append(exc)
            finally:
                simulate.exit()

        thread = threading.Thread(target=worker, name="motbo-physics", daemon=True)
        thread.start()
        simulate.render_loop()
        thread.join()
        simulate.destroy()
        self._simulate = None
        if error:
            raise error[0]

    def guard(self):
        if self._simulate is None:
            return nullcontext()
        return self._simulate.lock()

    def before_step(self) -> None:
        simulate = self._simulate
        if simulate is None:
            return
        while not simulate.run and not simulate.exitrequest:
            with simulate.lock():
                mujoco.mj_forward(self.model, self.data)
            time.sleep(0.01)

    def after_step(self) -> None:
        simulate = self._simulate
        if simulate is not None:
            simulate.add_to_history()

    def should_stop(self) -> bool:
        simulate = self._simulate
        return bool(simulate is not None and simulate.exitrequest)


def default_viewer_factory(model, data, model_path: str = "", run_id: str = "") -> SimulateViewer:
    return SimulateViewer(model, data, model_path, run_id)
