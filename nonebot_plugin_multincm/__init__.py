from nonebot.plugin import PluginMetadata

from . import __main__ as __main__
from .config import ConfigModel

__version__ = "0.1.0"
__plugin_meta__ = PluginMetadata(
    "MultiNCM",
    "网易云多选点歌",
    "指令：点歌 [歌曲名]",
    ConfigModel,
    {"License": "MIT", "Author": "student_2333"},
)
