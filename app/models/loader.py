from __future__ import annotations

from pathlib import Path

import mujoco


class ModelLoadError(Exception):
    pass


SUPPORTED_SUFFIXES = {".xml", ".mjb"}


def _resolve_model_path(path: str | Path) -> Path:
    model_path = Path(path)
    if not model_path.exists():
        raise ModelLoadError(f"模型文件不存在: {model_path}")
    if not model_path.is_file():
        raise ModelLoadError(f"模型路径不是文件: {model_path}")
    if model_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ModelLoadError(f"不支持的模型格式: {model_path.suffix}")
    return model_path.resolve()


def load_mj_model(path: str | Path) -> mujoco.MjModel:
    model_path = _resolve_model_path(path)
    try:
        if model_path.suffix.lower() == ".mjb":
            return mujoco.MjModel.from_binary_path(str(model_path))
        return mujoco.MjModel.from_xml_path(str(model_path))
    except ModelLoadError:
        raise
    except Exception as exc:
        raise ModelLoadError(f"模型无法加载: {model_path}: {exc}") from exc


def validate_mjcf(path: str | Path) -> Path:
    model_path = _resolve_model_path(path)
    load_mj_model(model_path)
    return model_path
