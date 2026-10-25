from pathlib import Path

import pytest

from app.core.config import DEFAULT_MODEL


@pytest.fixture
def example_model() -> Path:
    assert DEFAULT_MODEL.exists()
    return DEFAULT_MODEL
