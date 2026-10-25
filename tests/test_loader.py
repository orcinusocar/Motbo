from pathlib import Path

import pytest

from app.models.loader import ModelLoadError, validate_mjcf


def test_validate_example_model(example_model: Path) -> None:
    path = validate_mjcf(example_model)
    assert path == example_model.resolve()


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ModelLoadError, match="不存在"):
        validate_mjcf(tmp_path / "missing.xml")


def test_unsupported_suffix(tmp_path: Path) -> None:
    path = tmp_path / "robot.txt"
    path.write_text("not a model")
    with pytest.raises(ModelLoadError, match="不支持的模型格式"):
        validate_mjcf(path)


def test_invalid_xml(tmp_path: Path) -> None:
    path = tmp_path / "bad.xml"
    path.write_text("<mujoco><broken>")
    with pytest.raises(ModelLoadError, match="无法加载"):
        validate_mjcf(path)
