import asyncio as aio

from nonebot.adapters.onebot.v11 import (
    Message as OB11Msg,
    MessageSegment as OB11MsgSeg,
)

from .providers import BaseSong


async def to_card_message(song: BaseSong) -> OB11Msg:
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
