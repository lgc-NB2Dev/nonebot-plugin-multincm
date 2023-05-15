from nonebot.plugin import PluginMetadata

from . import __main__ as __main__
from .config import ConfigModel

__version__ = "0.2.2"
__plugin_meta__ = PluginMetadata(
    "MultiNCM",
    "网易云多选点歌",
    (
        "指令：\n"
        "▷ 点歌 [歌曲名 / 音乐 ID]\n"
        "▷ 解析 <回复 音乐卡片 / 链接>（获取该音乐的播放链接并使用自定义卡片发送）\n"
        "▷ 歌词 <回复 音乐卡片 / 链接>（获取该音乐的歌词）\n"
        "▷ 链接 <回复 音乐卡片 / 链接>（获取该音乐的网易云链接）\n"
        "\n"
        "Tip: 点击 Bot 发送的音乐卡片可以跳转直链，可以直接下载该音乐"
    ),
    ConfigModel,
    {"License": "MIT", "Author": "student_2333"},
)
