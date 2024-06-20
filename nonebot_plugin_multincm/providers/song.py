from typing import List
from typing_extensions import Optional, Self, override

from ..data_source import (
    get_track_audio,
    get_track_info,
    get_track_lrc,
    md,
    search_song,
)
from ..utils import format_alias, format_lrc
from .base import BaseSearcher, BaseSong, link_resolvable


@link_resolvable
class Song(BaseSong[md.Song]):
    calling = "歌曲"
    link_types = ("song", "url")

    @property
    @override
    def id(self) -> int:
        return self.info.id

    @classmethod
    @override
    async def from_id(cls, arg_id: int) -> Self:
        info = (await get_track_info([arg_id]))[0]
        if not info:
            raise ValueError("Song not found")
        return cls(info)

    @override
    async def get_playable_url(self) -> str:
        info = (await get_track_audio([self.info.id]))[0]
        return info.url

    @override
    async def get_name(self) -> str:
        return format_alias(self.info.name, self.info.alias)

    @override
    async def get_artists(self) -> List[str]:
        return [x.name for x in self.info.ar]

    @override
    async def get_cover_url(self) -> str:
        return self.info.al.pic_url

    @override
    async def get_lyric(self) -> Optional[str]:
        return format_lrc(await get_track_lrc(self.info.id))


class SongSearcher(BaseSearcher[md.SongSearchResult, md.Song, Song]):
    child_calling = "歌曲"

    @staticmethod
    @override
    async def search_from_id(arg_id: int) -> Optional[Song]:
        try:
            return await Song.from_id(arg_id)
        except ValueError:
            return None

    @override
    async def _extract_resp_content(
        self,
        resp: md.SongSearchResult,
    ) -> Optional[List[md.Song]]:
        return resp.songs

    @override
    async def _extract_total_count(self, resp: md.SongSearchResult) -> int:
        return resp.song_count

    @override
    async def _do_get_page(self, page: int) -> md.SongSearchResult:
        return await search_song(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.Song) -> Song:
        return Song(info=resp)
