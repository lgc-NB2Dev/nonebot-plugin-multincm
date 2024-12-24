import re
from dataclasses import dataclass
from typing import Annotated, Optional, Union
from typing_extensions import TypeAlias

from cachetools import TTLCache
from cookit import flatten, queued
from cookit.loguru import warning_suppress
from httpx import AsyncClient
from nonebot.adapters import Bot as BaseBot, Message as BaseMessage
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
from ..utils import is_song_card_supported
from .cache import get_cache

ExpectedTypeType: TypeAlias = Union[
    type[GeneralSongOrPlaylist],
    tuple[type[GeneralSongOrPlaylist], ...],
]


resolved_cache: TTLCache[int, "ResolveCache"] = TTLCache(
    config.ncm_resolve_cool_down_cache_size,
    config.ncm_resolve_cool_down,
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


def extract_song_card_hyper(
    msg: UniMessage,
    bot: Optional[BaseBot] = None,
) -> Optional[Hyper]:
    if (Hyper in msg) and is_song_card_supported(bot):
        return msg[Hyper, 0]
    return None


async def resolve_short_url(
    suffix: str,
    expected_type: Optional[ExpectedTypeType] = None,
    use_cool_down: bool = False,
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

    if it := await resolve_from_matched(matched, expected_type, use_cool_down):
        return it
    raise ValueError("Failed to resolve matched item url", expected_type)


async def resolve_from_matched(
    matched: re.Match[str],
    expected_type: Optional[ExpectedTypeType] = None,
    use_cool_down: bool = False,
) -> Optional[GeneralSongOrPlaylist]:
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
    expected_type: Optional[ExpectedTypeType] = None,
    use_cool_down: bool = False,
) -> Optional[GeneralSongOrPlaylist]:
    for regex in (SHORT_URL_REGEX, URL_REGEX):
        if m := re.search(regex, text, re.IGNORECASE):
            return await resolve_from_matched(m, expected_type, use_cool_down)
    return None


async def resolve_from_card(
    card: Hyper,
    resolve_playable: bool = True,
    expected_type: Optional[ExpectedTypeType] = None,
    use_cool_down: bool = False,
) -> Optional[GeneralSongOrPlaylist]:
    if not (raw := card.raw):
        return None

    is_playable_card = '"musicUrl"' in raw
    if (not resolve_playable) and is_playable_card:
        return None

    return await resolve_from_plaintext(raw, expected_type, use_cool_down)


async def resolve_from_msg(
    msg: UniMessage,
    resolve_playable_card: bool = True,
    expected_type: Optional[ExpectedTypeType] = None,
    use_cool_down: bool = False,
    bot: Optional[BaseBot] = None,
) -> Optional[GeneralSongOrPlaylist]:
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
    matcher: Matcher,
    expected_type: Optional[ExpectedTypeType] = None,
) -> GeneralSongOrPlaylist:
    regex_matched: Optional[re.Match[str]] = state.get(REGEX_MATCHED)
    if regex_matched:  # auto resolve
        if h := extract_song_card_hyper(msg, bot):
            if it := await resolve_from_card(
                h,
                resolve_playable=config.ncm_resolve_playable_card,
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
            Reply in msg
            and isinstance((reply_raw := msg[Reply, 0].msg), BaseMessage)
            and (reply_msg := await UniMessage.generate(message=reply_raw))
            and (it := await resolve_from_msg(reply_msg, expected_type=expected_type))
        )
        or (it := await resolve_from_msg(msg, expected_type=expected_type))
        or (it := await get_cache(expected_type=expected_type))
    ):
        return it

    await matcher.finish()  # noqa: RET503: NoReturn


async def dependency_resolve_from_ev(
    msg: UniMsg,
    state: T_State,
    bot: BaseBot,
    matcher: Matcher,
):
    return await resolve_from_ev_msg(msg, state, bot, matcher)


async def dependency_resolve_song_from_ev(
    msg: UniMsg,
    state: T_State,
    bot: BaseBot,
    matcher: Matcher,
):
    return await resolve_from_ev_msg(
        msg,
        state,
        bot,
        matcher,
        expected_type=tuple(registered_song),
    )


async def dependency_resolve_playlist_from_ev(
    msg: UniMsg,
    state: T_State,
    bot: BaseBot,
    matcher: Matcher,
):
    return await resolve_from_ev_msg(
        msg,
        state,
        bot,
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
