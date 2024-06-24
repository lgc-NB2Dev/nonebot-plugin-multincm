# ruff: noqa: E402

from nonebot import get_driver
from nonebot.plugin import PluginMetadata, inherit_supported_adapters, require

require("nonebot_plugin_alconna")
require("nonebot_plugin_waiter")
require("nonebot_plugin_htmlrender")

from . import interaction as interaction
from .config import ConfigModel, config
from .data_source import login, registered_searcher
from .interaction import load_commands

driver = get_driver()
driver.on_startup(login)

load_commands()

search_commands_help = "\n".join(
    [
        f"▶ {cmds[0]} [{(c := s.child_calling)}名 / {c} ID]\n"
        f"    ▷ 介绍：搜索{c}。当输入{c} ID 时会直接发送对应{c}\n"
        f"    ▷ 别名：{'、'.join(f'`{x}`' for x in cmds[1:])}"
        for s, cmds in registered_searcher.items()
    ],
)
upload_help = (
    (
        "▶ 上传 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：下载该音乐并上传到群文件\n"
        "    ▷ 别名：`upload`\n"
    )
    if not config.ncm_send_as_file
    else ""
)
auto_resolve_tip = (
    "▶ Bot 会自动解析你发送的网易云链接\n" if config.ncm_auto_resolve else ""
)

__version__ = "1.0.0a1"
__plugin_meta__ = PluginMetadata(
    name="MultiNCM",
    description="网易云多选点歌",
    usage=(
        "搜索指令：\n"
        f"{search_commands_help}"
        " \n"
        "操作指令：\n"
        "▶ 解析 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐信息并发送，也可以解析歌单等\n"
        "    ▷ 别名：`resolve`、`parse`、`get`\n"
        "▶ 直链 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的下载链接\n"
        "    ▷ 别名：`direct`\n"
        f"{upload_help}"
        "▶ 歌词 [回复 音乐卡片 / 链接]\n"
        "    ▷ 介绍：获取该音乐的歌词，以图片形式发送\n"
        "    ▷ 别名：`lrc`、`lyric`、`lyrics`\n"
        " \n"
        "Tip：\n"
        f"{auto_resolve_tip}"
        "▶ 点击 Bot 发送的音乐卡片会跳转到官网歌曲页\n"
        "▶ 使用需要回复音乐卡片的指令时，如果没有回复，会自动使用你触发发送的最近一个音乐卡片的信息"
    ),
    homepage="https://github.com/lgc-NB2Dev/nonebot-plugin-multincm",
    type="application",
    config=ConfigModel,
    supported_adapters=inherit_supported_adapters(
        "nonebot_plugin_alconna",
        "nonebot_plugin_waiter",
    ),
    extra={"License": "MIT", "Author": "student_2333"},
)
