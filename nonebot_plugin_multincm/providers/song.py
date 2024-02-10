from typing import List, Optional

from ..config import config
from ..const import MUSIC_LINK_TEMPLATE
from ..data_source import get_track_audio, get_track_info, get_track_lrc, search_song
from ..draw import Table, TableHead, TablePage
from ..types import Song as SongModel, SongSearchResult
from ..utils import format_alias, format_artists, format_lrc, format_time
from .base import BaseSearcher, BaseSong, searcher, song

CALLING = "歌曲"
LINK_TYPES = ["song", "url"]
COMMANDS = ["点歌", "网易云", "wyy"]


@song
class Song(BaseSong[SongModel]):
    calling = CALLING
    link_types = LINK_TYPES

    @property
    def song_id(self) -> int:
        return self.info.id

    @classmethod
    async def from_id(cls, song_id: int) -> "Song":
        info = (await get_track_info([song_id]))[0]
        if not info:
            raise ValueError("Song not found")
        return cls(info)

    async def get_url(self) -> str:
        return MUSIC_LINK_TEMPLATE.format(type=LINK_TYPES[0], id=self.info.id)

    async def get_playable_url(self) -> str:
        info = (await get_track_audio([self.info.id]))[0]
        return info.url

    async def get_name(self) -> str:
        return format_alias(self.info.name, self.info.alia)

    async def get_artists(self) -> List[str]:
        return [x.name for x in self.info.ar]

    async def get_cover_url(self) -> str:
        return self.info.al.picUrl

    async def get_lyric(self) -> Optional[str]:
        return format_lrc(await get_track_lrc(self.info.id))


@searcher
class SongSearcher(BaseSearcher[SongSearchResult, SongModel, Song]):
    calling = CALLING
    commands = COMMANDS

    @classmethod
    async def from_id(cls, arg_id: int) -> Optional[Song]:
        try:
            return await Song.from_id(arg_id)
        except ValueError:
            return None

    async def _build_list_resp(
        self,
        resp: SongSearchResult,
        page: int,
    ) -> TablePage:
        if not resp.songs:
            raise ValueError("No song in raw response")
        table = Table(
            [
                TableHead("序号", align="right"),
                TableHead("歌名", max_width=config.ncm_max_name_len),
                TableHead("歌手", max_width=config.ncm_max_artist_len),
                TableHead("时长", align="center"),
                TableHead("热度", align="center"),
            ],
            [
                [
                    f"[b]{i}[/b]",
                    format_alias(x.name, x.alia),
                    format_artists(x.ar),
                    format_time(x.dt),
                    f"{int(x.pop)}",
                ]
                for i, x in enumerate(resp.songs, self._calc_index_offset(page))
            ],
        )
        return TablePage(table, self.child_calling, page, resp.songCount)

    async def _extract_resp_content(
        self,
        resp: SongSearchResult,
    ) -> Optional[List[SongModel]]:
        return resp.songs

    async def _do_get_page(self, page: int) -> SongSearchResult:
        return await search_song(self.keyword, page=page)

    async def _build_selection(self, resp: SongModel) -> Song:
        return Song(info=resp)
