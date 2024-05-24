from pathlib import Path

MUSIC_LINK_TEMPLATE = "https://music.163.com/{type}?id={id}"

DATA_PATH = Path().cwd() / "data" / "multincm"
TEMP_PATH = DATA_PATH / "temp" / "multincm"
RES_DIR = Path(__file__).parent / "res"
for _p in (DATA_PATH, TEMP_PATH):
    _p.mkdir(parents=True, exist_ok=True)
