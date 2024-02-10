from pathlib import Path

MUSIC_LINK_TEMPLATE = "https://music.163.com/{type}?id={id}"  # noqa: RUF027


DATA_PATH = Path().cwd() / "data" / "multincm"
for _p in (DATA_PATH,):
    _p.mkdir(parents=True, exist_ok=True)

RES_DIR = Path(__file__).parent / "res"
