from nonebot.plugin import PluginMetadata

from . import __main__ as __main__  # noqa: E402
from .config import ConfigModel, config  # noqa: E402

auto_resolve_tip = "▶ Bot 会自动解析你发送的网易云链接\n"

__version__ = "0.5.0.dev8"
__plugin_meta__ = PluginMetadata(
    name="MultiNCM",
    description="网易云多选点歌",
    usage=(
        "搜索指令：\n"
        "▶ 点歌 [歌曲名 / 音乐 ID]\n"
        "    ▷ 介绍：搜索歌曲。当输入音乐 ID 时会直接发送对应音乐\n"
        "    ▷ 别名：`网易云`、`wyy`\n"
        "▶ 电台 [节目名 / 节目 ID]\n"
        "    ▷ 介绍：搜索电台节目。当输入电台 ID 时会直接发送对应节目\n"
        "    ▷ 别名：`声音`、`网易电台`、`wydt`、`wydj`\n"
        "▶ 歌单 [歌单名 / 歌单 ID]\n"
        "    ▷ 介绍：搜索歌单。当输入歌单 ID 时会直接发送对应歌单\n"
        "    ▷ 别名：`声音`、`网易电台`、`wydt`、`wydj`\n"
        " \n"
        "操作指令：\n"
        "▶ 解析 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的播放链接并使用自定义卡片发送\n"
        "    ▷ 别名：`resolve`、`parse`、`get`\n"
        "▶ 直链 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的下载链接\n"
        "    ▷ 别名：`direct`\n"
        "▶ 上传 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：下载该音乐并上传到群文件\n"
        "    ▷ 别名：`upload`\n"
        "▶ 歌词 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的歌词，以图片形式发送\n"
        "    ▷ 别名：`lrc`、`lyric`、`lyrics`\n"
        "▶ 语音 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：以语音的形式发送音乐\n"
        "    ▷ 别名：`record`\n"
        " \n"
        "Tip：\n"
        f"{auto_resolve_tip if config.ncm_auto_resolve else ''}"
        "▶ 点击 Bot 发送的音乐卡片会跳转到官网歌曲页\n"
        "▶ 使用需要回复音乐卡片的指令时，如果没有回复，会自动使用你触发发送的最近一个音乐卡片的信息"
    ),
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-multincm",
    type="application",
    config=ConfigModel,
    supported_adapters={"~onebot.v11"},
    extra={"License": "MIT", "Author": "student_2333"},
)
