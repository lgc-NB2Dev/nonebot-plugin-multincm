import asyncio as aio
from contextlib import suppress
from typing import TYPE_CHECKING, Literal, Optional, Union, cast
from typing_extensions import TypeAlias, TypeGuard

from httpx import AsyncClient
from nonebot import logger
from nonebot.adapters import Bot as BaseBot, Message as BaseMessage
from nonebot.matcher import current_bot

from ...config import config
from ...data_source import BaseSong

if TYPE_CHECKING:
    from nonebot.adapters.kritor import Bot as KritorBot, Message as KritorMsg
    from nonebot.adapters.onebot.v11 import Bot as OB11Bot, Message as OB11Msg

CardSendableBot: TypeAlias = Union["OB11Bot", "KritorBot"]
CardSendableEventType: TypeAlias = Literal["OneBot V11", "Kritor"]

CARD_SENDABLE_ADAPTERS = ["OneBot V11", "Kritor"]


def get_card_sendable_adapter_type(
    bot: Optional[BaseBot] = None,
) -> CardSendableEventType:
    if bot is None:
        bot = current_bot.get()
    if (n := bot.adapter.get_name()) in CARD_SENDABLE_ADAPTERS:
        return cast(CardSendableEventType, n)
    raise TypeError("This adapter is not supported")


def is_card_sendable_adapter(
    bot: Optional[BaseBot] = None,
) -> TypeGuard[CardSendableBot]:
    with suppress(TypeError):
        get_card_sendable_adapter_type(bot)
        return True
    return False


async def song_to_ob_v11_music_msg(song: BaseSong) -> "OB11Msg":
    from nonebot.adapters.onebot.v11 import (
        Message as OB11Msg,
        MessageSegment as OB11MsgSeg,
    )

    info, url = await aio.gather(song.get_info(), song.get_url())
    seg = OB11MsgSeg(
        "music",
        {
            "type": "custom",
            "url": url,
            "audio": info.playable_url,
            "title": info.display_name,
            "content": info.display_artists,
            "image": info.cover_url,
            "subtype": "163",  # gocq
            "voice": info.playable_url,  # gocq
            "jumpUrl": url,  # icqq
        },
    )
    return OB11Msg(seg)


async def song_to_kritor_music_msg(song: BaseSong) -> "KritorMsg":
    from nonebot.adapters.kritor import (
        Message as KritorMsg,
        MessageSegment as KritorMsgSeg,
    )

    info, url = await aio.gather(song.get_info(), song.get_url())
    seg = KritorMsgSeg.music(
        "custom",
        url,
        info.playable_url,
        info.display_name,
        info.display_artists,
        info.cover_url,
    )
    return KritorMsg(seg)


async def sign_music_card(song: BaseSong) -> str:
    assert config.ncm_card_sign_url
    info, url = await aio.gather(song.get_info(), song.get_url())
    async with AsyncClient(
        follow_redirects=True,
        timeout=config.ncm_card_sign_timeout,
    ) as cli:
        body = {
            "type": "custom",
            "url": url,
            "audio": info.playable_url,
            "title": info.display_name,
            "image": info.cover_url,
            "singer": info.display_artists,
        }
        return (
            (await cli.post(config.ncm_card_sign_url, json=body))
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
        event_type = get_card_sendable_adapter_type()

    card_json = None
    if config.ncm_card_sign_url:
        try:
            card_json = await sign_music_card(song)
        except Exception:
            logger.exception(f"Error occurred while signing music card for {song}")

    if card_json:
        transformer = {
            "OneBot V11": json_to_ob_v11_msg,
            "Kritor": json_to_kritor_msg,
        }[event_type]
        return await transformer(card_json)

    transformer = {
        "OneBot V11": song_to_ob_v11_music_msg,
        "Kritor": song_to_kritor_music_msg,
    }[event_type]
    return await transformer(song)
