import asyncio
import math
from pathlib import Path
from typing import TYPE_CHECKING, Optional, TypeVar
from typing_extensions import ParamSpec

from cookit import DebugFileWriter, flatten
from nonebot.adapters import Bot as BaseBot, Event as BaseEvent
from nonebot.matcher import current_bot
from nonebot.utils import run_sync
from nonebot_plugin_alconna.uniseg import SupportScope, UniMessage
from yarl import URL

from ..config import config

if TYPE_CHECKING:
    from ..data_source import md

P = ParamSpec("P")
TR = TypeVar("TR")

debug = DebugFileWriter(Path.cwd() / "debug", "multincm")


def format_time(time: int) -> str:
    ss, _ = divmod(time, 1000)
    mm, ss = divmod(ss, 60)
    return f"{mm:0>2d}:{ss:0>2d}"


def format_alias(name: str, alias: Optional[list[str]] = None) -> str:
    return f"{name}（{'；'.join(alias)}）" if alias else name


def format_artists(artists: list["md.Artist"]) -> str:
    return "、".join([x.name for x in artists])


def calc_page_number(index: int) -> int:
    return (index // config.ncm_list_limit) + 1


def calc_min_index(page: int) -> int:
    return (page - 1) * config.ncm_list_limit


def calc_min_max_index(page: int) -> tuple[int, int]:
    min_index = calc_min_index(page)
    max_index = min_index + config.ncm_list_limit
    return min_index, max_index


def calc_max_page(total: int) -> int:
    return math.ceil(total / config.ncm_list_limit)


def get_thumb_url(url: str, size: int = 64) -> str:
    return str(URL(url).update_query(param=f"{size}y{size}"))


def build_item_link(item_type: str, item_id: int) -> str:
    return f"https://music.163.com/{item_type}?id={item_id}"


def cut_string(text: str, length: int = 50) -> str:
    if len(text) <= length:
        return text
    return text[: length - 1] + "…"


async def ffmpeg_exists() -> bool:
    proc = await asyncio.create_subprocess_exec(
        config.ncm_ffmpeg_executable,
        "-version",
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    code = await proc.wait()
    return code == 0


async def encode_silk(path: "Path", rate: int = 24000) -> "Path":
    silk_path = path.with_suffix(".silk")
    if silk_path.exists():
        return silk_path

    pcm_path = path.with_suffix(".pcm")
    proc = await asyncio.create_subprocess_exec(
        config.ncm_ffmpeg_executable,
        "-y",
        "-i", str(path),
        "-f", "s16le", "-ar", f"{rate}", "-ac", "1", str(pcm_path),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )  # fmt: skip
    code = await proc.wait()
    if code != 0:
        raise RuntimeError(
            f"Failed to use ffmpeg to convert {path} to pcm, return code {code}",
        )

    try:
        from pysilk import encode

        await run_sync(encode)(pcm_path.open("rb"), silk_path.open("wb"), rate, rate)
    finally:
        pcm_path.unlink(missing_ok=True)

    return silk_path


def merge_alias(song: "md.Song") -> list[str]:
    alias = song.tns.copy() if song.tns else []
    alias.extend(
        x for x in flatten(x.split("；") for x in song.alias) if x not in alias
    )
    return alias


def is_song_card_supported(
    bot: Optional[BaseBot] = None,
    event: Optional[BaseEvent] = None,
) -> bool:
    if bot is None:
        bot = current_bot.get()
    s = UniMessage.get_target(event, bot).scope
    return bool(s and s == SupportScope.qq_client.value)
