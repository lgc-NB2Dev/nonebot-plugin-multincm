from cookit.nonebot.localstore import ensure_localstore_path_config
from nonebot_plugin_localstore import get_data_dir

ensure_localstore_path_config()

DATA_DIR = get_data_dir("multincm")
SONG_CACHE_DIR = DATA_DIR / "song_cache"

URL_REGEX = r"music\.163\.com/(.*?)(?P<type>[a-zA-Z]+)(/?\?id=|/)(?P<id>[0-9]+)&?"
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"
