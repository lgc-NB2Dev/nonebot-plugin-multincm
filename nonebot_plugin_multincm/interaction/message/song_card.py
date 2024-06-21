import asyncio as aio
from contextlib import suppress
from typing import TYPE_CHECKING, Literal, Optional, Union
from typing_extensions import TypeAlias, TypeGuard

from httpx import AsyncClient
from nonebot import logger
from nonebot.adapters import Event as BaseEvent, Message as BaseMessage
from nonebot.matcher import current_event

from ...config import config
from ...data_source import BaseSong

if TYPE_CHECKING:
    from nonebot.adapters.kritor import (
        Event as KritorEv,
        Message as KritorMsg,
    )
    from nonebot.adapters.onebot.v11 import Event as OB11Ev, Message as OB11Msg

CardSendableEvent: TypeAlias = Union["OB11Ev", "KritorEv"]
CardSendableEventType: TypeAlias = Literal["onebotv11", "kritor"]


def get_card_sendable_ev_type(ev: Optional[BaseEvent] = None) -> CardSendableEventType:
    if ev is None:
        ev = current_event.get()

    with suppress(ImportError):
        from nonebot.adapters.onebot.v11 import Event as OB11Ev

        if isinstance(ev, OB11Ev):
            return "onebotv11"

    with suppress(ImportError):
        from nonebot.adapters.kritor import Event as KritorEv

        if isinstance(ev, KritorEv):
            return "kritor"

    raise TypeError("This event is not supported")


def is_card_sendable_ev(ev: Optional[BaseEvent] = None) -> TypeGuard[CardSendableEvent]:
    with suppress(TypeError):
        get_card_sendable_ev_type(ev)
        return True
    return False


async def song_to_ob_v11_music_msg(song: BaseSong) -> "OB11Msg":
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


async def song_to_kritor_music_msg(song: BaseSong) -> "KritorMsg":
    from nonebot.adapters.kritor import (
        Message as KritorMsg,
        MessageSegment as KritorMsgSeg,
    )

    url, playable_url, name, artists, cover_url = await aio.gather(
        song.get_url(),
        song.get_playable_url(),
        song.get_name(),
        song.get_artists(),
        song.get_cover_url(),
    )
    content = "、".join(artists)
    seg = KritorMsgSeg.music("custom", url, playable_url, name, content, cover_url)
    return KritorMsg(seg)


async def sign_music_card(song: BaseSong) -> str:
    assert config.ncm_card_sign_url
    url, playable_url, name, artists, cover_url = await aio.gather(
        song.get_url(),
        song.get_playable_url(),
        song.get_name(),
        song.get_artists(),
        song.get_cover_url(),
    )
    content = "、".join(artists)
    async with AsyncClient(follow_redirects=True) as cli:
        return (
            (
                await cli.post(
                    config.ncm_card_sign_url,
                    json={
                        "type": "custom",
                        "url": url,
                        "audio": playable_url,
                        "title": name,
                        "image": cover_url,
                        "singer": content,
                    },
                )
            )
            .raise_for_status()
            .text
        )


async def json_to_ob_v11_msg(content: str) -> "OB11Msg":
    from nonebot.adapters.onebot.v11 import (
        Message as OB11Msg,
        MessageSegment as OB11MsgSeg,
    )

    return OB11Msg(OB11MsgSeg.json(content))


async def json_to_kritor_msg(content: str) -> "KritorMsg":
    from nonebot.adapters.kritor import (
        Message as KritorMsg,
        MessageSegment as KritorMsgSeg,
    )

    return KritorMsg(KritorMsgSeg.json(content))


async def get_song_card_msg(
    song: BaseSong,
    event_type: Optional[CardSendableEventType] = None,
) -> BaseMessage:
    if not event_type:
        event_type = get_card_sendable_ev_type()

    card_json = None
    if config.ncm_card_sign_url:
        try:
            card_json = await sign_music_card(song)
        except Exception:
            logger.exception(
                f"Error occurred while signing music card for {type(song).__name__}",
            )

    if card_json:
        transformers = {"onebotv11": json_to_ob_v11_msg, "kritor": json_to_kritor_msg}
        return await transformers[event_type](card_json)

    transformers = {
        "onebotv11": song_to_ob_v11_music_msg,
        "kritor": song_to_kritor_music_msg,
    }
    return await transformers[event_type](song)
