from typing import Any, List, Optional, cast

from ..config import config
from ..data_source import (
    get_offset_by_page_num,
    get_playlist_info,
    get_track_info,
    search_playlist,
)
from ..draw import Table, TableHead, TablePage
from ..types import (
    Playlist as PlaylistModel,
    PlaylistFromSearch,
    PlaylistSearchResult,
    Song as SongModel,
    SongSearchResult,
)
from .base import BasePlaylist, BaseSearcher, playlist, searcher
from .song import Song, SongSearcher

CALLING = "歌单"
CHILD_CALLING = Song.calling
COMMANDS = ["歌单", "playlist"]
LINK_TYPES = ["playlist"]


@playlist
class Playlist(BasePlaylist[PlaylistModel, SongModel, Song]):
    calling = CALLING
    child_calling = CHILD_CALLING
    link_types = LINK_TYPES

    info: PlaylistModel

    @property
    def playlist_id(self) -> int:
        return self.info.id

    def __init__(self, info: PlaylistModel, *args, **kwargs) -> None:
        self.info = info
        super().__init__(*args, **kwargs)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(playlist_id={self.playlist_id})"

    @classmethod
    async def from_id(cls, arg_id: int) -> "Playlist":
        resp = await get_playlist_info(arg_id)
        return cls(resp)

    async def _build_list_resp(self, resp: PlaylistModel, page: int) -> TablePage:
        if not resp.tracks:
            raise ValueError("Playlist is empty")
        fake_song_search_resp = SongSearchResult(
            searchQcReminder=None,
            songCount=resp.trackCount,
            songs=resp.tracks,
        )
        return await SongSearcher._build_list_resp(  # noqa: SLF001
            cast(Any, self),
            fake_song_search_resp,
            page,
        )

    async def _extract_resp_content(
        self,
        resp: PlaylistModel,
    ) -> List[SongModel]:
        return resp.tracks

    async def _do_get_page(self, page: int) -> PlaylistModel:
        offset = get_offset_by_page_num(page)
        track_ids = [
            x.id for x in self.info.trackIds[offset : offset + config.ncm_list_limit]
        ]
        tracks = await get_track_info(track_ids)
        kwargs = {**self.info.dict(by_alias=True), "tracks": tracks}
        return PlaylistModel(**kwargs)

    async def _build_selection(self, resp: SongModel) -> Song:
        return Song(info=resp)


@searcher
class PlaylistSearcher(
    BaseSearcher[PlaylistSearchResult, PlaylistFromSearch, Playlist],
):
    calling = CALLING
    commands = COMMANDS

    @classmethod
    async def from_id(cls, arg_id: int) -> Optional[Playlist]:
        try:
            return await Playlist.from_id(arg_id)
        except ValueError:
            return None

    async def _build_list_resp(
        self,
        resp: PlaylistSearchResult,
        page: int,
    ) -> TablePage:
        if not resp.playlists:
            raise ValueError("No song in raw response")
        table = Table(
            [
                TableHead("序号", align="right"),
                TableHead("歌单名", max_width=config.ncm_max_name_len),
                TableHead("创建者", max_width=config.ncm_max_artist_len),
                TableHead("歌曲数", align="center"),
                TableHead("播放数", align="center"),
                TableHead("收藏数", align="center"),
            ],
            [
                [
                    f"[b]{i}[/b]",
                    x.name,
                    x.creator.nickname,
                    f"{x.trackCount}",
                    f"{x.playCount}",
                    f"{x.bookCount}",
                ]
                for i, x in enumerate(resp.playlists, self._calc_index_offset(page))
            ],
        )
        return TablePage(table, self.child_calling, page, resp.playlistCount)

    async def _extract_resp_content(
        self,
        resp: PlaylistSearchResult,
    ) -> Optional[List[PlaylistFromSearch]]:
        return resp.playlists

    async def _do_get_page(self, page: int) -> PlaylistSearchResult:
        return await search_playlist(self.keyword, page=page)

    async def _build_selection(self, resp: PlaylistFromSearch) -> Playlist:
        return await Playlist.from_id(resp.id)
