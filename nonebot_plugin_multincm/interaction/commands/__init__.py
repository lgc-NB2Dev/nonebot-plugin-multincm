import importlib
from pathlib import Path


def load_commands():
    for module in Path(__file__).parent.iterdir():
        if module.name.startswith("_"):
            continue

        module = importlib.import_module(f".{module.stem}", __package__)
        assert module
