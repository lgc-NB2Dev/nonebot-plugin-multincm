from pathlib import Path

from cookit.nonebot.localstore import ensure_localstore_path_config
from nonebot_plugin_localstore import get_plugin_data_dir

ensure_localstore_path_config()

DATA_DIR = get_plugin_data_dir()
SONG_CACHE_DIR = DATA_DIR / "song_cache"

URL_REGEX = r"music\.163\.com/(.*?)(?P<type>[a-zA-Z]+)(/?\?id=|/)(?P<id>[0-9]+)&?"
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"

SESSION_FILE_NAME = "session.cache"
SESSION_FILE_PATH = DATA_DIR / SESSION_FILE_NAME


def migrate_old_data():
    old_data_dir = Path.cwd() / "data" / "multincm"
    if not old_data_dir.exists():
        return

    import shutil

    from nonebot import logger

    old_session_file_path = old_data_dir / SESSION_FILE_NAME
    if old_session_file_path.exists():
        shutil.move(old_session_file_path, SESSION_FILE_PATH)
        logger.info("已迁移旧登录态文件")

    shutil.rmtree(old_data_dir)
    logger.info("已删除旧缓存目录")


migrate_old_data()
