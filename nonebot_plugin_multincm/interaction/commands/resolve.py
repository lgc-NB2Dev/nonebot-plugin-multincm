from typing import Any, cast

from nonebot import on_command, on_regex
from nonebot.matcher import Matcher

from ...config import config
from ...const import SHORT_URL_REGEX, URL_REGEX
from ...data_source import BaseSongList
from ..cache import set_cache
from ..message import construct_info_msg
from ..resolver import IsAutoResolve, ResolvedItem
from .search import handle_song_or_list


async def resolve_handler(
    matcher: Matcher,
    result: ResolvedItem,
    is_auto_resolve: IsAutoResolve,
):
    result_it: Any = cast(Any, result)  # fuck that annoying weak type annotation
    if is_auto_resolve and isinstance(result, BaseSongList):
        await (await construct_info_msg(result_it, tip_command=True)).send()
    else:
        await handle_song_or_list(result_it, matcher, send_init_info=True)
    await set_cache(result_it)


def __register_resolve_matchers():
    matcher = on_command("解析", aliases={"resolve", "parse", "get"})
    matcher.handle()(resolve_handler)
    if config.ncm_auto_resolve:
        reg_matcher = on_regex(URL_REGEX)
        reg_matcher.handle()(resolve_handler)
        reg_short_matcher = on_regex(SHORT_URL_REGEX)
        reg_short_matcher.handle()(resolve_handler)


__register_resolve_matchers()
