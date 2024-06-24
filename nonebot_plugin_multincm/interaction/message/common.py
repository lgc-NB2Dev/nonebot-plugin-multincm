from cookit.loguru import warning_suppress
from nonebot.matcher import current_matcher

from ...config import config
from ...data_source import BaseSong
from ..cache import set_cache
from .info import construct_info_msg
from .song_card import get_song_card_msg, is_card_sendable_adapter
from .song_file import send_song_media


async def send_song(song: BaseSong):
    async def send():
        matcher = current_matcher.get()

        if config.ncm_send_as_card and is_card_sendable_adapter():
            with warning_suppress(f"Send {song} card failed"):
                await matcher.send(await get_song_card_msg(song))
                return

        receipt = ...
        with warning_suppress(f"Send {song} file failed"):
            receipt = await send_song_media(song)
        await (await construct_info_msg(song, tip_command=(receipt is ...))).send(
            reply_to=receipt.get_reply() if receipt and (receipt is not ...) else None,
        )

    await send()
    await set_cache(song)
