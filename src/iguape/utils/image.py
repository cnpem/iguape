from pathlib import Path
import os

ASSETS_PATH = Path(__file__).parent.parent.resolve() / "assets"


def get_assets(name: str):
    file_path = Path(ASSETS_PATH / name)
    exists = os.path.isfile(file_path)
    if exists:
        return str(file_path)
    else:
        raise OSError(f"File: {name} does not exists at {ASSETS_PATH}")
