import re
from dataclasses import dataclass
from typing import Annotated, TypeAlias

from cachetools import TTLCache
from cookit import flatten, queued
from cookit.loguru import warning_suppress
from cookit.nonebot.alconna import extract_reply_msg
from httpx import AsyncClient
from nonebot.adapters import Bot as BaseBot
from nonebot.consts import REGEX_MATCHED
from nonebot.params import Depends
from nonebot.typing import T_State
from nonebot_plugin_alconna import OriginalUniMsg
from nonebot_plugin_alconna.uniseg import Hyper, UniMessage

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
from ..utils import is_song_card_supported
from .cache import get_cache

ExpectedTypeType: TypeAlias = (
    type[GeneralSongOrPlaylist] | tuple[type[GeneralSongOrPlaylist], ...]
)


resolved_cache: TTLCache[int, "ResolveCache"] = TTLCache(
    config.resolve_cool_down_cache_size,
    config.resolve_cool_down,
)


@dataclass(eq=True, unsafe_hash=True)
class ResolveCache:
    link_type: str
    link_id: int


@queued
async def resolve_from_link_params_cool_down(link_type: str, link_id: int):
    cache = ResolveCache(link_type=link_type, link_id=link_id)
    cache_hash = hash(cache)

    if cache_hash in resolved_cache:
        resolved_cache[cache_hash] = cache  # flush ttl
        return None

    result = await resolve_from_link_params(link_type, link_id)
    resolved_cache[cache_hash] = cache
    return result


def check_is_expected_type(
    item_type: str,
    expected_type: ExpectedTypeType | None = None,
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


def extract_song_card_hyper(
    msg: UniMessage,
    bot: BaseBot | None = None,
) -> Hyper | None:
    if (Hyper in msg) and is_song_card_supported(bot):
        return msg[Hyper, 0]
    return None


async def resolve_short_url(
    suffix: str,
    expected_type: ExpectedTypeType | None = None,
    use_cool_down: bool = False,
) -> GeneralSongOrPlaylist:
    async with AsyncClient(base_url=SHORT_URL_BASE) as client:
        resp = await client.get(suffix, follow_redirects=False)

        if resp.status_code // 100 != 3:
            raise ValueError(
                f"Short url {suffix} returned invalid status code {resp.status_code}",
            )

        location = resp.headers.get("Location")
        if not location:
            raise ValueError(f"Short url {suffix} returned no location header")

    matched = re.search(URL_REGEX, location, re.IGNORECASE)
    if not matched:
        raise ValueError(
            f"Location {location} of short url {suffix} is not a song url",
        )

    if it := await resolve_from_matched(matched, expected_type, use_cool_down):
        return it
    raise ValueError("Failed to resolve matched item url", expected_type)


async def resolve_from_matched(
    matched: re.Match[str],
    expected_type: ExpectedTypeType | None = None,
    use_cool_down: bool = False,
) -> GeneralSongOrPlaylist | None:
    groups = matched.groupdict()

    if "suffix" in groups:
        suffix = groups["suffix"]
        with warning_suppress(f"Failed to resolve short url {suffix}"):
            return await resolve_short_url(suffix, expected_type, use_cool_down)

    elif "type" in groups and "id" in groups:
        link_type = groups["type"]
        if not check_is_expected_type(link_type, expected_type):
            return None
        link_id = groups["id"]
        with warning_suppress(f"Failed to resolve url {link_type}/{link_id}"):
            return await (
                resolve_from_link_params_cool_down
                if use_cool_down
                else resolve_from_link_params
            )(link_type, int(link_id))

    else:
        raise ValueError("Unknown regex match result passed in")

    return None


async def resolve_from_plaintext(
    text: str,
    expected_type: ExpectedTypeType | None = None,
    use_cool_down: bool = False,
) -> GeneralSongOrPlaylist | None:
    for regex in (SHORT_URL_REGEX, URL_REGEX):
        if m := re.search(regex, text, re.IGNORECASE):
            return await resolve_from_matched(m, expected_type, use_cool_down)
    return None


async def resolve_from_card(
    card: Hyper,
    resolve_playable: bool = True,
    expected_type: ExpectedTypeType | None = None,
    use_cool_down: bool = False,
) -> GeneralSongOrPlaylist | None:
    if not (raw := card.raw):
        return None

    is_playable_card = '"musicUrl"' in raw
    if (not resolve_playable) and is_playable_card:
        return None

    return await resolve_from_plaintext(raw, expected_type, use_cool_down)


async def resolve_from_msg(
    msg: UniMessage,
    resolve_playable_card: bool = True,
    expected_type: ExpectedTypeType | None = None,
    use_cool_down: bool = False,
    bot: BaseBot | None = None,
) -> GeneralSongOrPlaylist | None:
    if (h := extract_song_card_hyper(msg, bot)) and (
        it := await resolve_from_card(
            h,
            resolve_playable_card,
            expected_type,
        )
    ):
        return it
    return await resolve_from_plaintext(
        msg.extract_plain_text(),
        expected_type,
        use_cool_down,
    )


async def resolve_from_ev_msg(
    msg: UniMessage,
    state: T_State,
    bot: BaseBot,
    expected_type: ExpectedTypeType | None = None,
) -> GeneralSongOrPlaylist | None:
    regex_matched: re.Match[str] | None = state.get(REGEX_MATCHED)
    if regex_matched:  # auto resolve
        if h := extract_song_card_hyper(msg, bot):
            if it := await resolve_from_card(
                h,
                resolve_playable=config.resolve_playable_card,
                expected_type=expected_type,
                use_cool_down=True,
            ):
                return it

        elif it := await resolve_from_matched(
            regex_matched,
            expected_type=expected_type,
            use_cool_down=True,
        ):
            return it

    elif (  # common command trigger
        (
            (reply_msg := extract_reply_msg(msg))
            and (it := await resolve_from_msg(reply_msg, expected_type=expected_type))
        )
        or (it := await resolve_from_msg(msg, expected_type=expected_type))
        or (it := await get_cache(expected_type=expected_type))
    ):
        return it

    return None


async def dependency_resolve_from_ev(
    msg: OriginalUniMsg,
    state: T_State,
    bot: BaseBot,
):
    return await resolve_from_ev_msg(msg, state, bot)


async def dependency_resolve_song_from_ev(
    msg: OriginalUniMsg,
    state: T_State,
    bot: BaseBot,
):
    return await resolve_from_ev_msg(
        msg,
        state,
        bot,
        expected_type=tuple(registered_song),
    )


async def dependency_resolve_playlist_from_ev(
    msg: OriginalUniMsg,
    state: T_State,
    bot: BaseBot,
):
    return await resolve_from_ev_msg(
        msg,
        state,
        bot,
        expected_type=tuple(registered_playlist),
    )


async def dependency_is_auto_resolve(state: T_State) -> bool:
    return bool(state.get(REGEX_MATCHED))


ResolvedItem = Annotated[
    GeneralSongOrPlaylist | None,
    Depends(dependency_resolve_from_ev, use_cache=False),
]
ResolvedSong = Annotated[
    GeneralSong | None,
    Depends(dependency_resolve_song_from_ev, use_cache=False),
]
ResolvedPlaylist = Annotated[
    GeneralPlaylist | None,
    Depends(dependency_resolve_playlist_from_ev, use_cache=False),
]
IsAutoResolve = Annotated[bool, Depends(dependency_is_auto_resolve)]
