from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.config import DEFAULT_DATA_DIR, DEFAULT_MODEL
from app.core.types import RunConfig
from app.models.loader import ModelLoadError, validate_mjcf
from app.runs.manager import RunManager, RunNotFound


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="motbo", description="Motbo 仿真核心")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="校验 MJCF 模型")
    validate.add_argument("--model", default=str(DEFAULT_MODEL), help="模型文件路径")

    run = sub.add_parser("run", help="启动一次仿真")
    run.add_argument("--model", default=str(DEFAULT_MODEL), help="模型文件路径")
    run.add_argument("--duration", type=float, default=1.0, help="仿真时长（秒）")
    run.add_argument("--timestep", type=float, default=None, help="时间步长")
    run.add_argument("--seed", type=int, default=0, help="随机种子")
    run.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="数据目录")
    run.add_argument("--no-trajectory", action="store_true", help="不保存轨迹")
    run.add_argument("--render", action="store_true", help="用本次 run 的 MjData 打开 Viewer")

    status = sub.add_parser("status", help="查询运行状态")
    status.add_argument("run_id")
    status.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR), help="数据目录")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "validate":
        return _validate(args.model)
    if args.command == "run":
        return _run(args)
    if args.command == "status":
        return _status(args.run_id, args.data_dir)
    return 1


def _validate(model: str) -> int:
    try:
        path = validate_mjcf(model)
    except ModelLoadError as exc:
        print(f"校验失败: {exc}", file=sys.stderr)
        return 1
    print(f"模型可用: {path}")
    return 0


def _run(args: argparse.Namespace) -> int:
    config = RunConfig(
        duration=args.duration,
        timestep=args.timestep,
        seed=args.seed,
        save_trajectory=not args.no_trajectory,
        render=args.render,
    )
    with RunManager(data_dir=Path(args.data_dir)) as manager:
        record = manager.start(args.model, config)
        print(f"run_id={record.id} status={record.status.value}")
        record = manager.wait(record.id)
        print(json.dumps(record.to_dict(), indent=2, ensure_ascii=False))
        metrics = manager.metrics(record.id)
        if metrics:
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
        if record.status.value == "failed":
            return 1
    return 0


def _status(run_id: str, data_dir: str) -> int:
    with RunManager(data_dir=Path(data_dir)) as manager:
        try:
            record = manager.get(run_id)
        except RunNotFound as exc:
            print(f"查询失败: {exc}", file=sys.stderr)
            return 1
        print(json.dumps(record.to_dict(), indent=2, ensure_ascii=False))
        metrics = manager.metrics(run_id)
        if metrics:
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return 0
