from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_EXAMPLES_DIR = PROJECT_ROOT / "examples"
DEFAULT_MODEL = DEFAULT_EXAMPLES_DIR / "models" / "simple_arm.xml"
