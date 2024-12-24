from collections.abc import Iterable
from contextlib import suppress
from typing import Generic, Optional, TypeVar
from typing_extensions import Self, override

from ..utils import calc_min_max_index, cut_string, get_thumb_url
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
from .raw import get_playlist_info, get_track_info, md, search_playlist
from .song import Song, SongListPage

_TSongList = TypeVar("_TSongList", bound=BaseSongList)


class PlaylistListPage(
    BaseSongListPage[md.BasePlaylist, _TSongList],
    Generic[_TSongList],
):
    @override
    @classmethod
    async def transform_resp_to_list_card(cls, resp: md.BasePlaylist) -> ListPageCard:
        return ListPageCard(
            cover=get_thumb_url(resp.cover_img_url),
            title=resp.name,
            extras=[resp.creator.nickname],
            small_extras=[
                f"歌曲数 {resp.track_count} | "
                f"播放 {resp.play_count} | 收藏 {resp.book_count}",
            ],
        )


@playlist
class Playlist(BasePlaylist[md.Playlist, list[md.Song], md.Song, Song]):
    calling = "歌单"
    child_calling = Song.calling
    link_types = ("playlist",)

    @property
    @override
    def id(self) -> int:
        return self.info.id

    @classmethod
    @override
    async def from_id(cls, arg_id: int) -> Self:
        resp = await get_playlist_info(arg_id)
        return cls(resp)

    @override
    async def _extract_resp_content(self, resp: list[md.Song]) -> list[md.Song]:
        return resp

    @override
    async def _extract_total_count(self, resp: list[md.Song]) -> int:
        return self.info.track_count

    @override
    async def _do_get_page(self, page: int) -> list[md.Song]:
        min_index, max_index = calc_min_max_index(page)
        track_ids = [x.id for x in self.info.track_ids[min_index:max_index]]
        return await get_track_info(track_ids)

    @override
    async def _build_selection(self, resp: md.Song) -> Song:
        return Song(info=resp)

    @override
    async def _build_list_page(self, resp: Iterable[md.Song]) -> SongListPage[Self]:
        return SongListPage(resp, self)

    @override
    async def get_name(self) -> str:
        return self.info.name

    @override
    async def get_creators(self) -> list[str]:
        return [self.info.creator.nickname]

    @override
    async def get_cover_url(self) -> str:
        return self.info.cover_img_url

    @override
    @classmethod
    async def format_description(cls, info: PlaylistInfo) -> str:
        if not cls.is_info_from_cls(info):
            raise TypeError("Info is not from this class")
        base_desc = await super().format_description(info)
        self = info.father
        lst_desc = f"\n{cut_string(d)}" if (d := self.info.description) else ""
        return (
            f"{base_desc}\n"
            f"播放 {self.info.play_count} | "
            f"收藏 {self.info.book_count} | "
            f"评论 {self.info.comment_count} | "
            f"分享 {self.info.share_count}"
            f"{lst_desc}"
        )


@searcher
class PlaylistSearcher(
    BaseSearcher[md.PlaylistSearchResult, md.BasePlaylist, Playlist],
):
    child_calling = Playlist.calling
    commands = ("网易歌单", "wygd", "wypli")

    @override
    @staticmethod
    async def search_from_id(arg_id: int) -> Optional[Playlist]:
        with suppress(Exception):
            return await Playlist.from_id(arg_id)
        return None

    @override
    async def _extract_resp_content(
        self,
        resp: md.PlaylistSearchResult,
    ) -> Optional[list[md.BasePlaylist]]:
        return resp.playlists

    @override
    async def _extract_total_count(self, resp: md.PlaylistSearchResult) -> int:
        return resp.playlist_count

    @override
    async def _do_get_page(self, page: int) -> md.PlaylistSearchResult:
        return await search_playlist(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.BasePlaylist) -> Playlist:
        return await Playlist.from_id(resp.id)

    @override
    async def _build_list_page(
        self,
        resp: Iterable[md.BasePlaylist],
    ) -> PlaylistListPage[Self]:
        return PlaylistListPage(resp, self)
