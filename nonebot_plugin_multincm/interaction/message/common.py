from contextlib import suppress

from cookit.loguru.common import logged_suppress
from nonebot.matcher import current_matcher

from ...config import config
from ...data_source import BaseSong
from ..cache import set_cache
from .info import construct_info_msg
from .song_card import get_card_sendable_ev_type, get_song_card_msg


async def send_song(song: BaseSong):
    async def send():
        matcher = current_matcher.get()

        if config.ncm_use_card:
            ev_type = None
            with suppress(TypeError):
                ev_type = get_card_sendable_ev_type()
            if ev_type:
                with logged_suppress(
                    f"Send {type(song).__name__} {song.id} card failed",
                ):
                    await matcher.send(await get_song_card_msg(song, ev_type))
                    return

        await (await construct_info_msg(song)).send()

    await send()
    await set_cache(song)
