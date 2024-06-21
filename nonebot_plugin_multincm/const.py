from pathlib import Path

DATA_DIR = Path.cwd() / "data" / "multincm"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True)

DEBUG_ROOT_DIR = Path.cwd() / "debug"
DEBUG_DIR = DEBUG_ROOT_DIR / "multincm"
