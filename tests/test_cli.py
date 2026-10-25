from pathlib import Path

from app.cli import build_parser, main


def test_validate_example_model(example_model: Path) -> None:
    assert main(["validate", "--model", str(example_model)]) == 0


def test_validate_missing_model(tmp_path: Path) -> None:
    assert main(["validate", "--model", str(tmp_path / "missing.xml")]) == 1


def test_run_parser_has_render_flag() -> None:
    args = build_parser().parse_args(["run", "--duration", "10", "--render"])
    assert args.render is True
    args = build_parser().parse_args(["run"])
    assert args.render is False


def test_cli_headless_run(tmp_path: Path, example_model: Path) -> None:
    assert (
        main(
            [
                "run",
                "--model",
                str(example_model),
                "--duration",
                "0.04",
                "--data-dir",
                str(tmp_path),
            ]
        )
        == 0
    )
    runs = list((tmp_path / "runs").iterdir())
    assert runs
    assert (runs[0] / "metrics.json").exists()
