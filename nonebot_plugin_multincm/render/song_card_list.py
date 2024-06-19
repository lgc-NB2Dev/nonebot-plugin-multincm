import asyncio
from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired, Unpack

from cookit import to_b64_url
from httpx import AsyncClient

from ..data_source import md
from ..providers import GeneralSongList, SongListInnerResp
from ..utils import calc_min_index, format_artists, format_time
from .utils import render_html, render_template


@dataclass
class CardDesc:
    content: str
    type: Optional[Literal["title", "small"]] = None

    @classmethod
    def normal(cls, content: str) -> "CardDesc":
        return cls(content)

    @classmethod
    def title(cls, content: str) -> "CardDesc":
        return cls(content, "title")

    @classmethod
    def small(cls, content: str) -> "CardDesc":
        return cls(content, "small")


@dataclass
class CardItem:
    cover: str
    desc: List[CardDesc]

    @classmethod
    async def build(cls, cover: str, desc: List[CardDesc]) -> "CardItem":
        if cover.startswith(("http://", "https://")):
            async with AsyncClient(follow_redirects=True) as cli:
                resp = (await cli.get(cover)).raise_for_status()
                cover = to_b64_url(resp.content, resp.headers["Content-Type"])
        return cls(cover, desc)


class CardListRenderParams(TypedDict):
    title: str
    cards: List[CardItem]
    page_current: int
    page_max: int
    total_count: int
    index_offset: NotRequired[int]


async def render_card_list(**kwargs: Unpack[CardListRenderParams]) -> bytes:
    if kwargs.get("index_offset") is None:
        kwargs["index_offset"] = 0
    return await render_html(
        await render_template("song_card_list.html.jinja", **kwargs),
    )


async def transform_song_resp(resp: md.Song) -> CardItem:
    return CardItem(
        cover=resp.al.pic_url,
        desc=[
            CardDesc.title(resp.name),
            CardDesc.normal(format_artists(resp.ar)),
            CardDesc.small(f"{format_time(resp.dt)} | 热度 {resp.pop}"),
        ],
    )


async def transform_voice_resp(resp: md.VoiceResource) -> CardItem:
    info = resp.base_info
    return CardItem(
        cover=info.cover_url,
        desc=[
            CardDesc.title(info.name),
            CardDesc.normal(info.radio.name),
            CardDesc.small(
                f"{format_time(info.duration)} | "
                f"播放 {info.listener_count} | 点赞 {info.liked_count}",
            ),
        ],
    )


async def transform_playlist_resp(resp: md.PlaylistFromSearch) -> CardItem:
    return CardItem(
        cover=resp.cover_img_url,
        desc=[
            CardDesc.title(resp.name),
            CardDesc.normal(resp.creator.nickname),
            CardDesc.small(
                f"歌曲数 {resp.track_count} | "
                f"播放 {resp.play_count} | 收藏 {resp.book_count}",
            ),
        ],
    )


async def render_list_resp(
    searcher: GeneralSongList,
    resp: List[SongListInnerResp],
) -> bytes:
    transformers = {
        md.Song: transform_song_resp,
        md.VoiceResource: transform_voice_resp,
        md.PlaylistFromSearch: transform_playlist_resp,
    }
    params = {
        "title": f"{searcher.child_calling}列表",
        "cards": await asyncio.gather(*(transformers[type(r)](r) for r in resp)),
        "page_current": searcher.current_page,
        "page_max": searcher.max_page,
        "total_count": searcher.total_count,
        "index_offset": calc_min_index(searcher.current_page),
    }
    return await render_card_list(**params)
