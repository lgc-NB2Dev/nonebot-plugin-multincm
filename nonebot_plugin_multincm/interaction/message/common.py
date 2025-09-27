import asyncio
from cookit.loguru import warning_suppress
from nonebot_plugin_alconna.uniseg import UniMessage
from cookit.nonebot.alconna import RecallContext
from nonebot.matcher import current_bot

from ...config import config
from ...data_source import BasePlaylist, BaseSong
from ...utils import is_song_card_supported
from ..cache import set_cache
from .song_card import send_song_card_msg
from .song_file import send_song_media

SONG_TIP = "\n使用指令 `direct` 获取播放链接"
PLAYLIST_TIP = "\n使用指令 `resolve` 选择内容播放"


async def construct_info_msg(
    it: BaseSong | BasePlaylist,
    tip_command: bool = True,
) -> UniMessage:
    tip = (
        next(
            v
            for k, v in {BaseSong: SONG_TIP, BasePlaylist: PLAYLIST_TIP}.items()
            if isinstance(it, k)
        )
        if tip_command
        else ""
    )
    info = await it.get_info()
    desc = await info.get_description()
    bot = current_bot.get()
    adapter_name = bot.adapter.get_name()
    if adapter_name in ["QQ"]:
        return UniMessage.image(url=info.cover_url) + f"\n{desc}\n{tip}"
    return UniMessage.image(url=info.cover_url) + f"{desc}\n{info.url}{tip}"


async def send_song(song: BaseSong):
    recall = RecallContext(delay=config.ncm_delete_msg_delay)
    await recall.send(UniMessage.text("处理中，请稍等哦～"))

    async def send():
        if config.ncm_send_as_card and is_song_card_supported():
            with warning_suppress(f"Send {song} card failed"):
                await send_song_card_msg(song)
                return

        receipt = ...
        if config.ncm_send_media:
            with warning_suppress(f"Send {song} file failed"):
                receipt = await send_song_media(song)
        await (await construct_info_msg(song, tip_command=(receipt is ...))).send(
            reply_to=receipt.get_reply() if receipt and (receipt is not ...) else None,
        )

    await send()
    asyncio.create_task(recall.recall())
    await set_cache(song)
