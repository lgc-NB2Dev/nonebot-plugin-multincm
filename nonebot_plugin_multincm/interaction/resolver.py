import re
import time
from dataclasses import dataclass
from typing import Optional, Tuple, Type, Union
from typing_extensions import Annotated, TypeAlias

from cachetools import TTLCache
from cookit import flatten, queued
from cookit.loguru import warning_suppress
from httpx import AsyncClient
from nonebot.adapters import Message as BaseMessage
from nonebot.consts import REGEX_MATCHED
from nonebot.matcher import Matcher
from nonebot.params import Depends
from nonebot.typing import T_State
from nonebot_plugin_alconna import UniMsg
from nonebot_plugin_alconna.uniseg import Hyper, Reply, UniMessage

from ..config import config
from ..const import SHORT_URL_BASE, SHORT_URL_REGEX, URL_REGEX
from ..data_source import (
    GeneralPlaylist,
    GeneralSong,
    GeneralSongOrPlaylist,
    registered_playlist,
    registered_song,
    resolve_from_link_params,
)
from .cache import get_cache

ExpectedTypeType: TypeAlias = Union[
    Type[GeneralSongOrPlaylist],
    Tuple[Type[GeneralSongOrPlaylist], ...],
]

resolved_cache: TTLCache[float, "ResolveCache"] = TTLCache(
    config.ncm_resolve_cool_down_cache_size,
    config.ncm_resolve_cool_down,
)


@dataclass(eq=True)
class ResolveCache:
    link_type: str
    link_id: int


@queued
async def resolve_from_link_params_cool_down(link_type: str, link_id: int):
    cache = ResolveCache(link_type=link_type, link_id=link_id)
    for k in resolved_cache:
        if resolved_cache[k] == cache:
            resolved_cache[k] = cache  # flush ttl
            return None

    result = await resolve_from_link_params(link_type, link_id)
    resolved_cache[time.time()] = cache
    return result


def check_is_expected_type(
    item_type: str,
    expected_type: Optional[ExpectedTypeType] = None,
) -> bool:
    if not expected_type:
        return True
    expected = flatten(
        x.link_types
        for x in (
            (expected_type) if isinstance(expected_type, tuple) else (expected_type,)
        )
    )
    return item_type in expected


async def resolve_short_url(
    suffix: str,
    expected_type: Optional[ExpectedTypeType] = None,
) -> GeneralSongOrPlaylist:
    async with AsyncClient(base_url=SHORT_URL_BASE) as client:
        resp = await client.get(suffix, follow_redirects=False)

        if resp.status_code // 100 != 3:
            raise ValueError(
                f"Short url {suffix} "
                f"returned invalid status code {resp.status_code}",
            )

        location = resp.headers.get("Location")
        if not location:
            raise ValueError(f"Short url {suffix} returned no location header")

    matched = re.search(URL_REGEX, location, re.IGNORECASE)
    if not matched:
        raise ValueError(
            f"Location {location} of short url {suffix} is not a song url",
        )

    if it := await resolve_from_matched(matched):
        return it
    raise ValueError("Failed to resolve matched item url", expected_type)


async def resolve_from_matched(
    matched: re.Match[str],
    expected_type: Optional[ExpectedTypeType] = None,
) -> Optional[GeneralSongOrPlaylist]:
    groups = matched.groupdict()

    if "suffix" in groups:
        suffix = groups["suffix"]
        with warning_suppress(f"Failed to resolve short url {suffix}"):
            return await resolve_short_url(suffix, expected_type)

    elif "type" in groups and "id" in groups:
        link_type = groups["type"]
        if not check_is_expected_type(link_type, expected_type):
            return None
        link_id = groups["id"]
        with warning_suppress(f"Failed to resolve url {link_type}/{link_id}"):
            return await resolve_from_link_params_cool_down(link_type, int(link_id))

    else:
        raise ValueError("Unknown regex match result passed in")

    return None


async def resolve_from_plaintext(
    text: str,
    expected_type: Optional[ExpectedTypeType] = None,
) -> Optional[GeneralSongOrPlaylist]:
    for regex in (SHORT_URL_REGEX, URL_REGEX):
        if m := re.search(regex, text, re.IGNORECASE):
            return await resolve_from_matched(m, expected_type)
    return None


async def resolve_from_card(
    card: Hyper,
    resolve_playable: bool = True,
    expected_type: Optional[ExpectedTypeType] = None,
) -> Optional[GeneralSongOrPlaylist]:
    if not (raw := card.raw):
        return None

    is_playable_card = '"musicUrl"' in raw
    if (not resolve_playable) and is_playable_card:
        return None

    return await resolve_from_plaintext(raw, expected_type)


async def resolve_from_msg(
    msg: UniMessage,
    resolve_playable_card: bool = True,
    expected_type: Optional[ExpectedTypeType] = None,
) -> Optional[GeneralSongOrPlaylist]:
    if (Hyper in msg) and (
        it := await resolve_from_card(
            msg[Hyper, 0],
            resolve_playable_card,
            expected_type,
        )
    ):
        return it
    return await resolve_from_plaintext(msg.extract_plain_text(), expected_type)


async def resolve_from_ev_msg(
    msg: UniMessage,
    state: T_State,
    matcher: Matcher,
    expected_type: Optional[ExpectedTypeType] = None,
) -> GeneralSongOrPlaylist:
    regex_matched: Optional[re.Match[str]] = state.get(REGEX_MATCHED)
    if regex_matched:  # auto resolve
        if Hyper in msg:
            if it := await resolve_from_card(
                msg[Hyper, 0],
                resolve_playable=config.ncm_resolve_playable_card,
                expected_type=expected_type,
            ):
                return it
            await matcher.finish()
        if it := await resolve_from_matched(regex_matched):
            return it
        await matcher.finish()

    if (
        Reply in msg
        and isinstance((reply_raw := msg[Reply, 0].msg), BaseMessage)
        and (reply_msg := await UniMessage.generate(message=reply_raw))
        and (it := await resolve_from_msg(reply_msg, expected_type=expected_type))
    ):
        return it

    if it := await resolve_from_msg(msg, expected_type=expected_type):
        return it

    if it := await get_cache(expected_type=expected_type):
        return it

    await matcher.finish()  # noqa: RET503


async def dependency_resolve_from_ev(
    msg: UniMsg,
    state: T_State,
    matcher: Matcher,
):
    return await resolve_from_ev_msg(msg, state, matcher)


async def dependency_resolve_song_from_ev(
    msg: UniMsg,
    state: T_State,
    matcher: Matcher,
):
    return await resolve_from_ev_msg(
        msg,
        state,
        matcher,
        expected_type=tuple(registered_song),
    )


async def dependency_resolve_playlist_from_ev(
    msg: UniMsg,
    state: T_State,
    matcher: Matcher,
):
    return await resolve_from_ev_msg(
        msg,
        state,
        matcher,
        expected_type=tuple(registered_playlist),
    )


async def dependency_is_auto_resolve(state: T_State) -> bool:
    return bool(state.get(REGEX_MATCHED))


ResolvedItem = Annotated[
    GeneralSongOrPlaylist,
    Depends(dependency_resolve_from_ev, use_cache=False),
]
ResolvedSong = Annotated[
    GeneralSong,
    Depends(dependency_resolve_song_from_ev, use_cache=False),
]
ResolvedPlaylist = Annotated[
    GeneralPlaylist,
    Depends(dependency_resolve_playlist_from_ev, use_cache=False),
]
IsAutoResolve = Annotated[bool, Depends(dependency_is_auto_resolve)]
