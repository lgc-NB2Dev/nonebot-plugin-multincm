from contextlib import suppress
from typing import List, Optional
from typing_extensions import Self, override

from cookit.pyd import model_dump

from ..utils import calc_min_max_index
from .base import BasePlaylist, BaseSearcher, playlist, searcher
from .raw import get_playlist_info, get_track_info, md, search_playlist
from .song import Song


@playlist
class Playlist(BasePlaylist[md.Playlist, md.Song, Song]):
    child_calling = "歌曲"
    link_types = ("playlist",)

    def __init__(self, info: md.Playlist) -> None:
        super().__init__(info)

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
    async def _extract_resp_content(
        self,
        resp: md.Playlist,
    ) -> List[md.Song]:
        return resp.tracks

    @override
    async def _extract_total_count(self, resp: md.Playlist) -> int:
        return resp.track_count

    @override
    async def _do_get_page(self, page: int) -> md.Playlist:
        min_index, max_index = calc_min_max_index(page)
        track_ids = [x.id for x in self.info.track_ids[min_index:max_index]]
        tracks = await get_track_info(track_ids)
        kwargs = {**model_dump(self.info, by_alias=True), "tracks": tracks}
        return md.Playlist(**kwargs)

    @override
    async def _build_selection(self, resp: md.Song) -> Song:
        return Song(info=resp)


@searcher
class PlaylistSearcher(
    BaseSearcher[md.PlaylistSearchResult, md.PlaylistFromSearch, Playlist],
):
    child_calling = "歌单"
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
    ) -> Optional[List[md.PlaylistFromSearch]]:
        return resp.playlists

    @override
    async def _extract_total_count(self, resp: md.PlaylistSearchResult) -> int:
        return resp.playlist_count

    @override
    async def _do_get_page(self, page: int) -> md.PlaylistSearchResult:
        return await search_playlist(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.PlaylistFromSearch) -> Playlist:
        return await Playlist.from_id(resp.id)
