from typing import Union

from cookit.loguru import warning_suppress
from nonebot.matcher import current_matcher
from nonebot_plugin_alconna.uniseg import UniMessage

from ...config import config
from ...data_source import BasePlaylist, BaseSong
from ..cache import set_cache
from .song_card import get_song_card_msg, is_card_sendable_adapter
from .song_file import send_song_media

SONG_TIP = "\n使用指令 `direct` 获取播放链接"
PLAYLIST_TIP = "\n使用指令 `resolve` 选择内容播放"


async def construct_info_msg(
    it: Union[BaseSong, BasePlaylist],
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
    return UniMessage.image(info.cover_url) + f"{desc}\n{info.url}{tip}"


async def send_song(song: BaseSong):
    async def send():
        matcher = current_matcher.get()

        if config.ncm_send_as_card and is_card_sendable_adapter():
            with warning_suppress(f"Send {song} card failed"):
                await matcher.send(await get_song_card_msg(song))
                return

        receipt = ...
        if config.ncm_send_media:
            with warning_suppress(f"Send {song} file failed"):
                receipt = await send_song_media(song)
        await (await construct_info_msg(song, tip_command=(receipt is ...))).send(
            reply_to=receipt.get_reply() if receipt and (receipt is not ...) else None,
        )

    await send()
    await set_cache(song)
