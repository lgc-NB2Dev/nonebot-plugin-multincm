from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_apscheduler")

from . import __main__ as __main__  # noqa: E402
from .config import ConfigModel  # noqa: E402

__version__ = "0.3.5"
__plugin_meta__ = PluginMetadata(
    name="MultiNCM",
    description="网易云多选点歌",
    usage=(
        "指令列表：\n"
        "▶ 点歌 [歌曲名 / 音乐 ID]\n"
        "    ▷ 介绍：搜索歌曲。当输入音乐 ID 时会直接发送对应音乐\n"
        "    ▷ 别名：`网易云`、`wyy`\n"
        "▶ 电台 [歌曲名 / 节目 ID]\n"
        "    ▷ 介绍：搜索电台节目。当输入电台 ID 时会直接发送对应节目\n"
        "    ▷ 别名：`声音`、`网易电台`、`wydt`、`wydj`\n"
        "▶ 解析 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的播放链接并使用自定义卡片发送\n"
        "    ▷ 别名：`resolve`、`parse`、`get`\n"
        "▶ 歌词 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的歌词，以图片形式发送\n"
        "    ▷ 别名：`lrc`、`lyric`、`lyrics`\n"
        "▶ 链接 [回复 音乐卡片]\n"
        "    ▷ 介绍：获取 Bot 发送的音乐卡片的网易云歌曲链接\n"
        "    ▷ 别名：`link`、`url`\n"
        " \n"
        "Tip：\n"
        "▶ 点击 Bot 发送的音乐卡片会跳转到音乐直链，可以直接下载\n"
        "▶ 使用需要回复音乐卡片的指令时，如果没有回复，会自动使用你触发发送的最近一个音乐卡片的信息"
    ),
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-multincm",
    type="application",
    config=ConfigModel,
    supported_adapters=["~onebot.v11"],
    extra={"License": "MIT", "Author": "student_2333"},
)
