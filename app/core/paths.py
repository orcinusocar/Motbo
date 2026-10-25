from __future__ import annotations

import re
from pathlib import Path

RUN_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class PathGuardError(ValueError):
    pass


def ensure_within(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise PathGuardError(f"路径超出允许目录: {resolved}")
    return resolved


def validate_run_id(run_id: str) -> str:
    if not RUN_ID_RE.match(run_id):
        raise PathGuardError(f"非法 run_id: {run_id}")
    return run_id
