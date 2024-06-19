import asyncio as aio
from contextlib import suppress
from typing import TYPE_CHECKING, Optional
from typing_extensions import TypeGuard

from nonebot.adapters import Event as BaseEvent
from nonebot.matcher import current_event

from ..providers import BaseSong

if TYPE_CHECKING:
    from nonebot.adapters.onebot.v11 import Event as OB11Ev, Message as OB11Msg


def is_ob_v11_ev(ev: Optional[BaseEvent] = None) -> TypeGuard["OB11Ev"]:
    if ev is None:
        ev = current_event.get()

    with suppress(ImportError):
        from nonebot.adapters.onebot.v11 import Event as OB11Ev

        return isinstance(ev, OB11Ev)

    return False


async def song_to_ob_v11_card_msg(song: BaseSong) -> "OB11Msg":
    from nonebot.adapters.onebot.v11 import (
        Message as OB11Msg,
        MessageSegment as OB11MsgSeg,
    )

    url, playable_url, name, artists, cover_url = await aio.gather(
        song.get_url(),
        song.get_playable_url(),
        song.get_name(),
        song.get_artists(),
        song.get_cover_url(),
    )
    content = "、".join(artists)
    seg = OB11MsgSeg(
        "music",
        {
            "type": "custom",
            "url": url,
            "audio": playable_url,
            "title": name,
            "content": content,
            "image": cover_url,
            "subtype": "163",  # gocq
            "voice": playable_url,  # gocq
            "jumpUrl": url,  # icqq
        },
    )
    return OB11Msg(seg)
