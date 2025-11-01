import mimetypes
from typing import TYPE_CHECKING, Any, Literal, cast

from cookit.loguru import log_exception_warning, warning_suppress
from httpx import AsyncClient
from nonebot import logger
from nonebot.exception import NetworkError
from nonebot.matcher import current_bot, current_event
from nonebot_plugin_alconna.uniseg import Receipt, UniMessage

from ...config import config
from ...const import SONG_CACHE_DIR
from ...utils import encode_silk, ffmpeg_exists

if TYPE_CHECKING:
    from ...data_source import BaseSong, SongInfo


async def ensure_ffmpeg():
    if await ffmpeg_exists():
        return
    logger.warning(
        "FFmpeg 无法使用，插件将不会把音乐文件转为 silk 格式提交给协议端",
    )
    raise TypeError("FFmpeg unavailable, fallback to UniMessage")


def get_download_path(info: "SongInfo"):
    return SONG_CACHE_DIR / info.download_filename


async def download_song(info: "SongInfo"):
    file_path = get_download_path(info)
    if file_path.exists():
        return file_path

    async with AsyncClient(follow_redirects=True) as cli, cli.stream("GET", info.playable_url) as resp:  # fmt: skip
        resp.raise_for_status()
        SONG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with file_path.open("wb") as f:
            async for chunk in resp.aiter_bytes():
                f.write(chunk)
    return file_path


async def send_song_media_uni_msg(
    info: "SongInfo",
    raw: bool = False,
    as_file: bool = False,
):
    path = get_download_path(info)
    mime = t[0] if (t := mimetypes.guess_type(path.name)) else None
    kw_f = {"raw": path.read_bytes()} if raw else {"path": path}
    kw: Any = {**kw_f, "name": info.display_filename, "mimetype": mime}
    msg = UniMessage.file(**kw) if as_file else UniMessage.audio(**kw)
    return await msg.send(fallback=False)


async def send_song_voice_silk_uni_msg(info: "SongInfo"):
    await ensure_ffmpeg()
    return await UniMessage.voice(
        raw=(await encode_silk(get_download_path(info))).read_bytes(),
    ).send()


async def send_song_media_telegram(info: "SongInfo", as_file: bool = False):  # noqa: ARG001
    return await send_song_media_uni_msg(info, as_file=False)


async def _send_song_file_onebot_v11(info: "SongInfo"):
    from nonebot.adapters.onebot.v11 import (
        Bot as OB11Bot,
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    bot = cast("OB11Bot", current_bot.get())
    event = current_event.get()

    if not isinstance(event, GroupMessageEvent | PrivateMessageEvent):
        raise TypeError("Event not supported")

    file = (
        str(get_download_path(info).resolve())
        if config.ob_v11_local_mode
        else cast(
            "str",
            (await bot.download_file(url=info.playable_url))["file"],
        )
    )

    if isinstance(event, PrivateMessageEvent):
        await bot.upload_private_file(
            user_id=event.user_id,
            file=file,
            name=info.display_filename,
        )
    else:
        await bot.upload_group_file(
            group_id=event.group_id,
            file=file,
            name=info.display_filename,
        )


async def send_song_media_onebot_v11(info: "SongInfo", as_file: bool = False):
    if as_file:
        try:
            return await _send_song_file_onebot_v11(info)
        except NetworkError as e:
            # maybe just upload timeout, we ignore it
            logger.info(f"Ignored NetworkError: {e}")
            return None
        except Exception as e:
            log_exception_warning(e, f"Send {info} as file failed")
            if config.ob_v11_ignore_send_file_failure:
                return None
            logger.warning("Falling back to voice message")

    return await send_song_voice_silk_uni_msg(info)


async def send_song_media_qq(info: "SongInfo", as_file: bool = False):  # noqa: ARG001
    return await send_song_voice_silk_uni_msg(info)


async def send_song_media_platform_specific(
    info: "SongInfo",
    as_file: bool = False,
) -> Receipt | None | Literal[False]:
    bot = current_bot.get()
    adapter_name = bot.adapter.get_name()
    processors = {
        "Telegram": send_song_media_telegram,
        "OneBot V11": send_song_media_onebot_v11,
        "QQ": send_song_media_qq,
    }
    if adapter_name not in processors:
        return False
    return await processors[adapter_name](info, as_file=as_file)


async def send_song_media(song: "BaseSong", as_file: bool | None = None):
    if as_file is None:
        as_file = config.send_as_file

    info = await song.get_info()
    try:
        await download_song(info)
    except Exception as e:
        log_exception_warning(e, f"Failed to download song {song}")
        return None

    with warning_suppress(f"Failed to send {song} using platform specific method"):
        r = await send_song_media_platform_specific(info, as_file=as_file)
        if (r is not False) or config.send_media_no_unimsg_fallback:
            return r or None
        logger.warning("Falling back to UniMessage")

    with warning_suppress(
        f"Failed to send {song} using file path, fallback using raw bytes",
    ):
        return await send_song_media_uni_msg(info, raw=False, as_file=as_file)
    return await send_song_media_uni_msg(info, raw=True, as_file=as_file)
