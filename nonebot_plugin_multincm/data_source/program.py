from collections.abc import Iterable
from typing import Generic, Optional, TypeVar
from typing_extensions import Self, override

from ..utils import cut_string, format_time, get_thumb_url
from .base import (
    BaseSearcher,
    BaseSong,
    BaseSongList,
    BaseSongListPage,
    ListPageCard,
    SongInfo,
    searcher,
    song,
)
from .raw import get_program_info, get_track_audio, md, search_program

_TSongList = TypeVar("_TSongList", bound=BaseSongList)


class ProgramListPage(
    BaseSongListPage[md.ProgramBaseInfo, _TSongList],
    Generic[_TSongList],
):
    @override
    @classmethod
    async def transform_resp_to_list_card(
        cls,
        resp: md.ProgramBaseInfo,
    ) -> ListPageCard:
        return ListPageCard(
            cover=get_thumb_url(resp.cover_url),
            title=resp.name,
            extras=[resp.radio.name],
            small_extras=[
                (
                    f"{format_time(resp.duration)} | "
                    f"播放 {resp.listener_count} | 点赞 {resp.liked_count}"
                ),
            ],
        )


@song
class Program(BaseSong[md.ProgramBaseInfo]):
    calling = "声音"
    link_types = ("program", "dj")

    @property
    @override
    def id(self) -> int:
        return self.info.id

    @classmethod
    @override
    async def from_id(cls, arg_id: int) -> Self:
        info = await get_program_info(arg_id)
        if not info:
            raise ValueError("Voice not found")
        return cls(info)

    @override
    async def get_name(self) -> str:
        return self.info.name

    @override
    async def get_alias(self) -> Optional[list[str]]:
        return None

    @override
    async def get_artists(self) -> list[str]:
        return [self.info.radio.name]

    @override
    async def get_duration(self) -> int:
        return self.info.duration

    @override
    async def get_cover_url(self) -> str:
        return self.info.cover_url

    @override
    async def get_playable_url(self) -> str:
        song_id = self.info.main_track_id
        info = (await get_track_audio([song_id]))[0]
        return info.url

    @override
    async def get_lyrics(self) -> None:
        return None

    @override
    @classmethod
    async def format_description(cls, info: SongInfo) -> str:
        if not cls.is_info_from_cls(info):
            raise TypeError("Info is not from this class")
        self = info.father
        p_desc = f"\n{cut_string(d)}" if (d := self.info.description) else ""
        return (
            f"{cls.calling}：{self.info.name}\n"
            f"电台：{self.info.radio.name}\n"
            f"台主：{self.info.dj.nickname}\n"
            f"时长 {info.display_duration} | "
            f"播放 {self.info.listener_count} | "
            f"点赞 {self.info.liked_count} | "
            f"评论 {self.info.comment_count} | "
            f"分享 {self.info.share_count}"
            f"{p_desc}"
        )


@searcher
class ProgramSearcher(
    BaseSearcher[md.ProgramSearchResult, md.ProgramBaseInfo, Program],
):
    child_calling = Program.calling
    commands = ("网易声音", "wysy", "wyprog")

    @staticmethod
    @override
    async def search_from_id(arg_id: int) -> Optional[Program]:
        try:
            return await Program.from_id(arg_id)
        except ValueError:
            return None

    @override
    async def _extract_resp_content(
        self,
        resp: md.ProgramSearchResult,
    ) -> Optional[list[md.ProgramBaseInfo]]:
        return [x.base_info for x in resp.resources] if resp.resources else None

    @override
    async def _extract_total_count(self, resp: md.ProgramSearchResult) -> int:
        return resp.total_count

    @override
    async def _do_get_page(self, page: int) -> md.ProgramSearchResult:
        return await search_program(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.ProgramBaseInfo) -> Program:
        return Program(info=resp)

    @override
    async def _build_list_page(
        self,
        resp: Iterable[md.ProgramBaseInfo],
    ) -> ProgramListPage[Self]:
        return ProgramListPage(resp, self)
