from pathlib import Path

DATA_PATH = Path().cwd() / "data" / "multincm"
for _p in (DATA_PATH,):
    _p.mkdir(parents=True, exist_ok=True)

FILE_CACHE_PATH = DATA_PATH / "file_cache.json"

RES_DIR = Path(__file__).parent / "res"


MUSIC_LINK_TEMPLATE = "https://music.163.com/{type}?id={id}"
