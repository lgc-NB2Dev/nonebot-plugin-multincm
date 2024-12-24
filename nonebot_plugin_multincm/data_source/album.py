from collections.abc import Iterable
from contextlib import suppress
from typing import Generic, Optional, TypeVar
from typing_extensions import Self, override

from ..utils import calc_min_max_index, format_artists, get_thumb_url
from .base import (
    BasePlaylist,
    BaseSearcher,
    BaseSongList,
    BaseSongListPage,
    ListPageCard,
    PlaylistInfo,
    playlist,
    searcher,
)
from .raw import get_album_info, md, search_album
from .song import Song, SongListPage

_TSongList = TypeVar("_TSongList", bound=BaseSongList)


class AlbumListPage(BaseSongListPage[md.Album, _TSongList], Generic[_TSongList]):
    @override
    @classmethod
    async def transform_resp_to_list_card(cls, resp: md.Album) -> ListPageCard:
        return ListPageCard(
            cover=get_thumb_url(resp.pic_url),
            title=resp.name,
            extras=[format_artists(resp.artists)],
            small_extras=[f"歌曲数 {resp.size}"],
        )


@playlist
class Album(BasePlaylist[md.AlbumInfo, list[md.Song], md.Song, Song]):
    calling = "专辑"
    child_calling = Song.calling
    link_types = ("album",)

    @property
    @override
    def id(self) -> int:
        return self.info.album.id

    @classmethod
    @override
    async def from_id(cls, arg_id: int) -> Self:
        resp = await get_album_info(arg_id)
        return cls(resp)

    @override
    async def _extract_resp_content(self, resp: list[md.Song]) -> list[md.Song]:
        return resp

    @override
    async def _extract_total_count(self, resp: list[md.Song]) -> int:
        return self.info.album.size

    @override
    async def _do_get_page(self, page: int) -> list[md.Song]:
        min_index, max_index = calc_min_max_index(page)
        return self.info.songs[min_index:max_index]

    @override
    async def _build_selection(self, resp: md.Song) -> Song:
        return Song(info=resp)

    @override
    async def _build_list_page(self, resp: Iterable[md.Song]) -> SongListPage[Self]:
        return SongListPage(resp, self)

    @override
    async def get_name(self) -> str:
        return self.info.album.name

    @override
    async def get_creators(self) -> list[str]:
        return [x.name for x in self.info.album.artists]

    @override
    async def get_cover_url(self) -> str:
        return self.info.album.pic_url

    @override
    @classmethod
    async def format_description(cls, info: PlaylistInfo) -> str:
        if not cls.is_info_from_cls(info):
            raise TypeError("Info is not from this class")
        base_desc = await super().format_description(info)
        self = info.father
        return f"{base_desc}\n歌曲数 {self.info.album.size}"


@searcher
class AlbumSearcher(BaseSearcher[md.AlbumSearchResult, md.Album, Album]):
    child_calling = Album.calling
    commands = ("网易专辑", "wyzj", "wyal")

    @override
    @staticmethod
    async def search_from_id(arg_id: int) -> Optional[Album]:
        with suppress(Exception):
            return await Album.from_id(arg_id)
        return None

    @override
    async def _extract_resp_content(
        self,
        resp: md.AlbumSearchResult,
    ) -> Optional[list[md.Album]]:
        return resp.albums

    @override
    async def _extract_total_count(self, resp: md.AlbumSearchResult) -> int:
        return resp.album_count

    @override
    async def _do_get_page(self, page: int) -> md.AlbumSearchResult:
        return await search_album(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.Album) -> Album:
        return await Album.from_id(resp.id)

    @override
    async def _build_list_page(self, resp: Iterable[md.Album]) -> AlbumListPage[Self]:
        return AlbumListPage(resp, self)
