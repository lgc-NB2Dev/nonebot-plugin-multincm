import mimetypes
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, cast

from cookit.loguru import warning_suppress
from httpx import AsyncClient
from nonebot.matcher import current_bot, current_event
from nonebot_plugin_alconna.uniseg import Receipt, UniMessage, get_exporter

from ...config import config
from ...const import SONG_CACHE_DIR
from ...data_source import BaseSong, SongInfo


async def download_song(info: SongInfo):
    filename = info.download_filename
    file_path = SONG_CACHE_DIR / filename
    if not file_path.exists():
        async with AsyncClient(follow_redirects=True) as cli:
            async with cli.stream("GET", info.playable_url) as resp:
                resp.raise_for_status()
                with file_path.open("wb") as f:
                    async for chunk in resp.aiter_bytes():
                        f.write(chunk)
    return file_path


async def send_song_media_uni_msg(
    path: Path,
    info: SongInfo,
    raw: bool = False,
    as_file: bool = False,
):
    mime = t[0] if (t := mimetypes.guess_type(path.name)) else None
    kw_f = {"raw": path.read_bytes()} if raw else {"path": path}
    kw: Any = {**kw_f, "name": info.display_filename, "mimetype": mime}
    msg = UniMessage.file(**kw) if as_file else UniMessage.audio(**kw)
    return await msg.send(fallback=False)


async def get_current_ev_receipt(msg_ids: Any):
    bot = current_bot.get()
    ev = current_event.get()
    exporter = get_exporter(bot)
    if not exporter:
        raise TypeError("This adapter is not supported")
    return Receipt(
        bot=bot,
        context=ev,
        exporter=exporter,
        msg_ids=msg_ids if isinstance(msg_ids, list) else [msg_ids],
    )


async def send_song_media_telegram(info: SongInfo, as_file: bool = False):  # noqa: ARG001
    return await send_song_media_uni_msg(await download_song(info), info, as_file=False)


async def send_song_media_onebot_v11(info: SongInfo, as_file: bool = False):
    if not as_file:
        raise TypeError("Should fallback using UniMessage")

    from nonebot.adapters.onebot.v11 import (
        Bot as OB11Bot,
        GroupMessageEvent,
        MessageEvent,
        PrivateMessageEvent,
    )

    bot = cast(OB11Bot, current_bot.get())
    event = cast(MessageEvent, current_event.get())

    file = (
        (await download_song(info))
        if config.ncm_ob_v11_local_mode
        else cast(str, (await bot.download_file(url=info.playable_url))["file"])
    )

    if isinstance(event, PrivateMessageEvent):
        await bot.upload_private_file(
            user_id=event.user_id,
            file=file,
            name=info.display_filename,
        )
    elif isinstance(event, GroupMessageEvent):
        await bot.upload_group_file(
            group_id=event.group_id,
            file=file,
            name=info.display_filename,
        )
    else:
        raise TypeError("Event not supported")


async def send_song_media_platform_specific(
    info: SongInfo,
    as_file: bool = False,
) -> Optional[Receipt]:
    bot = current_bot.get()
    adapter_name = bot.adapter.get_name()
    processors = {
        "Telegram": send_song_media_telegram,
        "OneBot V11": send_song_media_onebot_v11,
    }
    if adapter_name not in processors:
        raise TypeError("This adapter is not supported")
    return await processors[adapter_name](info, as_file=as_file)


async def send_song_media(song: BaseSong, as_file: bool = config.ncm_send_as_file):
    info = await song.get_info()

    with warning_suppress(
        f"Failed to send {song} using platform specific method, fallback to UniMessage",
    ):
        with suppress(TypeError):
            return await send_song_media_platform_specific(info, as_file=as_file)

    path = await download_song(info)
    with warning_suppress(
        f"Failed to send {song} use file path, will try to send using raw bytes",
    ):
        if not TYPE_CHECKING:
            return await send_song_media_uni_msg(path, info, raw=False, as_file=as_file)
    return await send_song_media_uni_msg(path, info, raw=True, as_file=as_file)
