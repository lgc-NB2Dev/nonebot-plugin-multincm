import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, TypedDict
from typing_extensions import NotRequired, Unpack, override

from ..data_source import GeneralSongListPage, md
from ..utils import calc_min_index, format_artists, format_time, get_thumb_url
from .utils import render_html, render_template


class BaseCard(ABC):
    @abstractmethod
    async def render(self, index: int) -> str: ...


@dataclass
class TrackCard(BaseCard):
    cover: str
    title: str
    alias: str = ""
    extras: List[str] = field(default_factory=list)
    small_extras: List[str] = field(default_factory=list)

    @override
    async def render(self, index: int) -> str:
        return await render_template(
            "track_card.html.jinja",
            index=index,
            **self.__dict__,
        )


class CardListRenderParams(TypedDict):
    title: str
    cards: List[BaseCard]
    current_page: int
    max_page: int
    total_count: int
    index_offset: NotRequired[int]


async def render_card_list(**kwargs: Unpack[CardListRenderParams]) -> bytes:
    index_offset = kwargs.get("index_offset", 0)
    new_kwargs = {
        **kwargs,
        "cards": await asyncio.gather(
            *(c.render(i) for i, c in enumerate(kwargs["cards"], 1 + index_offset)),
        ),
    }
    return await render_html(
        await render_template("card_list.html.jinja", **new_kwargs),
    )


async def transform_song_resp(resp: md.Song) -> TrackCard:
    return TrackCard(
        cover=get_thumb_url(resp.al.pic_url, 64),
        title=resp.name,
        alias="；".join(resp.alias),
        extras=[format_artists(resp.ar)],
        small_extras=[f"{format_time(resp.dt)} | 热度 {resp.pop}"],
    )


async def transform_voice_resp(resp: md.VoiceResource) -> TrackCard:
    info = resp.base_info
    return TrackCard(
        cover=get_thumb_url(info.cover_url, 64),
        title=info.name,
        extras=[info.radio.name],
        small_extras=[
            (
                f"{format_time(info.duration)} | "
                f"播放 {info.listener_count} | 点赞 {info.liked_count}"
            ),
        ],
    )


async def transform_playlist_resp(resp: md.PlaylistFromSearch) -> TrackCard:
    return TrackCard(
        cover=get_thumb_url(resp.cover_img_url, 64),
        title=resp.name,
        extras=[resp.creator.nickname],
        small_extras=[
            f"歌曲数 {resp.track_count} | "
            f"播放 {resp.play_count} | 收藏 {resp.book_count}",
        ],
    )


async def render_list_resp(resp: GeneralSongListPage) -> bytes:
    transformers = {
        md.Song: transform_song_resp,
        md.VoiceResource: transform_voice_resp,
        md.PlaylistFromSearch: transform_playlist_resp,
    }
    params: CardListRenderParams = {
        "title": f"{resp.father.child_calling}列表",
        "cards": await asyncio.gather(*(transformers[type(r)](r) for r in resp)),
        "current_page": resp.father.current_page,
        "max_page": resp.father.max_page,
        "total_count": resp.father.total_count,
        "index_offset": calc_min_index(resp.father.current_page),
    }
    return await render_card_list(**params)
