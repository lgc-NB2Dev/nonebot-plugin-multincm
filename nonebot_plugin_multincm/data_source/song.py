from collections.abc import Iterable
from typing import Generic, Optional, TypeVar
from typing_extensions import Self, override

from ..utils import (
    format_artists,
    format_time,
    get_thumb_url,
    merge_alias,
    normalize_lrc,
)
from .base import (
    BaseSearcher,
    BaseSong,
    BaseSongList,
    BaseSongListPage,
    ListPageCard,
    searcher,
    song,
)
from .raw import get_track_audio, get_track_info, get_track_lrc, md, search_song

_TSongList = TypeVar("_TSongList", bound=BaseSongList)


class SongListPage(BaseSongListPage[md.Song, _TSongList], Generic[_TSongList]):
    @override
    @classmethod
    async def transform_resp_to_list_card(cls, resp: md.Song) -> ListPageCard:
        return ListPageCard(
            cover=get_thumb_url(resp.al.pic_url),
            title=resp.name,
            alias="；".join(merge_alias(resp)),
            extras=[format_artists(resp.ar)],
            small_extras=[f"{format_time(resp.dt)} | 热度 {resp.pop}"],
        )


@song
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
    async def get_name(self) -> str:
        return self.info.name

    @override
    async def get_alias(self) -> list[str]:
        return merge_alias(self.info)

    @override
    async def get_artists(self) -> list[str]:
        return [x.name for x in self.info.ar]

    @override
    async def get_duration(self) -> int:
        return self.info.dt

    @override
    async def get_cover_url(self) -> str:
        return self.info.al.pic_url

    @override
    async def get_playable_url(self) -> str:
        info = (await get_track_audio([self.info.id]))[0]
        return info.url

    @override
    async def get_lyrics(self) -> Optional[list[list[str]]]:
        return normalize_lrc(await get_track_lrc(self.info.id))


@searcher
class SongSearcher(BaseSearcher[md.SongSearchResult, md.Song, Song]):
    child_calling = Song.calling
    commands = ("点歌", "网易云", "wyy", "网易点歌", "wydg", "wysong")

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
    ) -> Optional[list[md.Song]]:
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

    @override
    async def _build_list_page(
        self,
        resp: Iterable[md.Song],
    ) -> SongListPage[Self]:
        return SongListPage(resp, self)
