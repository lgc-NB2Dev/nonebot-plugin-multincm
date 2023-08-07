from math import ceil

from nonebot import require

from ..config import config
from ..msg_cache import CALLING_MAP
from ..types import SearchResult, SongSearchResult
from .shared import get_song_search_res_table, get_voice_search_res_table

if config.ncm_use_playwright:
    require("nonebot_plugin_htmlrender")

    from .playwright import draw_search_res as draw_search_res_base
    from .playwright import str_to_pic as str_to_pic

else:
    from .pil import draw_search_res as draw_search_res_base
    from .pil import str_to_pic as str_to_pic


async def draw_search_res(res: SearchResult, page_num: int = 1) -> bytes:
    is_song = isinstance(res, SongSearchResult)
    calling = CALLING_MAP["song" if is_song else "voice"]

    index_offset = (page_num - 1) * config.ncm_list_limit
    head, lines = (
        get_song_search_res_table(res, index_offset)
        if is_song
        else get_voice_search_res_table(res, index_offset)
    )

    max_count = res.songCount if is_song else res.totalCount
    max_page = ceil(max_count / config.ncm_list_limit)

    return await draw_search_res_base(
        calling,
        page_num,
        max_page,
        max_count,
        head,
        lines,
    )
