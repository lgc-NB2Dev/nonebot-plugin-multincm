from pathlib import Path

DATA_PATH = Path().cwd() / "data" / "multincm"
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True)

RES_DIR = Path(__file__).parent / "res"


MUSIC_LINK_TEMPLATE = "https://music.163.com/{type}?id={id}"
