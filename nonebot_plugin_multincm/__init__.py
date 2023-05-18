from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_apscheduler")

from . import __main__ as __main__  # noqa: E402
from .config import ConfigModel  # noqa: E402

__version__ = "0.2.5"
__plugin_meta__ = PluginMetadata(
    "MultiNCM",
    "网易云多选点歌",
    (
        "指令列表\n"
        "▶ 点歌 [歌曲名 / 音乐 ID]\n"
        "    ▷ 介绍：顾名思义。当输入音乐 ID 时会直接发送对应音乐\n"
        "    ▷ 别名：`网易云`、`wyy`\n"
        "▶ 解析 <回复 音乐卡片 / 链接>\n"
        "    ▷ 介绍：获取该音乐的播放链接并使用自定义卡片发送\n"
        "    ▷ 别名：`resolve`、`parse`、`get`\n"
        "▶ 歌词 <回复 音乐卡片 / 链接>\n"
        "    ▷ 介绍：获取该音乐的歌词，以图片形式发送\n"
        "    ▷ 别名：`lrc`、`lyric`、`lyrics`\n"
        "▶ 链接 <回复 音乐卡片>\n"
        "    ▷ 介绍：获取 Bot 发送的音乐卡片的网易云歌曲链接\n"
        "    ▷ 别名：`link`、`url`\n"
        " \n"
        "Tip: 点击 Bot 发送的音乐卡片会跳转到音乐直链，可以直接下载"
    ),
    ConfigModel,
    {"License": "MIT", "Author": "student_2333"},
)
