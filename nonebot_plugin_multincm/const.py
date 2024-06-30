from pathlib import Path

from nonebot_plugin_alconna.uniseg import SupportAdapter

DATA_DIR = Path.cwd() / "data" / "multincm"
SONG_CACHE_DIR = DATA_DIR / "song_cache"
for _p in (DATA_DIR, SONG_CACHE_DIR):
    _p.mkdir(parents=True, exist_ok=True)

DEBUG_ROOT_DIR = Path.cwd() / "debug"
DEBUG_DIR = DEBUG_ROOT_DIR / "multincm"

URL_REGEX = r"music\.163\.com/(.*?)(?P<type>[a-zA-Z]+)(/?\?id=|/)(?P<id>[0-9]+)&?"
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"

MUSIC_CARD_SUPPORT_ADAPTERS = (
    SupportAdapter.onebot11.value,
    SupportAdapter.kritor.value,
    SupportAdapter.mirai_official.value,
    SupportAdapter.mirai_community.value,
)
