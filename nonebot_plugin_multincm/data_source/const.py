from pathlib import Path

DATA_PATH = Path().cwd() / "data" / "multincm"
TEMP_PATH = DATA_PATH / "temp" / "multincm"
RES_DIR = Path(__file__).parent / "res"
for _p in (DATA_PATH, TEMP_PATH):
    _p.mkdir(parents=True, exist_ok=True)


def build_item_link(item_type: str, item_id: int) -> str:
    return f"https://music.163.com/{item_type}?id={item_id}"
