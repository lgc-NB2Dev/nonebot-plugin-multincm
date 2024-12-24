import asyncio
from typing import TYPE_CHECKING, TypedDict
from typing_extensions import Unpack

from ..utils import calc_min_index
from .utils import render_html, render_template

if TYPE_CHECKING:
    from ..data_source import GeneralSongListPage


class CardListRenderParams(TypedDict):
    title: str
    cards: list[str]
    current_page: int
    max_page: int
    total_count: int


class TrackCardRenderParams(TypedDict):
    index: int
    cover: str
    title: str
    alias: str
    extras: list[str]
    small_extras: list[str]


async def render_card_list(**kwargs: Unpack[CardListRenderParams]) -> bytes:
    return await render_html(await render_template("card_list.html.jinja", **kwargs))


async def render_track_card_html(**kwargs: Unpack[TrackCardRenderParams]) -> str:
    return await render_template("track_card.html.jinja", **kwargs)


async def render_list_resp(resp: "GeneralSongListPage") -> bytes:
    index_offset = calc_min_index(resp.father.current_page)
    card_params = [
        {"index": i, **x.__dict__}
        for i, x in enumerate(await resp.transform_to_list_cards(), index_offset + 1)
    ]
    cards = await asyncio.gather(*(render_track_card_html(**x) for x in card_params))
    return await render_card_list(
        title=f"{resp.father.child_calling}列表",
        cards=cards,
        current_page=resp.father.current_page,
        max_page=resp.father.max_page,
        total_count=resp.father.total_count,
    )
