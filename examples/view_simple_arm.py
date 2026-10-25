"""Visualize the example arm through motbo run --render."""

from pathlib import Path

from app.cli import main

MODEL_PATH = Path(__file__).resolve().parent / "models" / "simple_arm.xml"

if __name__ == "__main__":
    raise SystemExit(
        main(
            [
                "run",
                "--model",
                str(MODEL_PATH),
                "--duration",
                "10",
                "--render",
            ]
        )
    )
