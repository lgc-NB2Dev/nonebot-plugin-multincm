from collections.abc import Iterable
from contextlib import suppress
from typing import Generic, Optional, TypeVar
from typing_extensions import Self, override

from ..utils import cut_string, get_thumb_url
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
from .program import Program, ProgramListPage
from .raw import get_radio_info, get_radio_programs, md, search_radio

_TSongList = TypeVar("_TSongList", bound=BaseSongList)


class RadioListPage(
    BaseSongListPage[md.RadioBaseInfo, _TSongList],
    Generic[_TSongList],
):
    @override
    @classmethod
    async def transform_resp_to_list_card(
        cls,
        resp: md.RadioBaseInfo,
    ) -> ListPageCard:
        return ListPageCard(
            cover=get_thumb_url(resp.pic_url),
            title=resp.name,
            extras=[resp.dj.nickname],
            small_extras=[
                f"节目数 {resp.program_count} | "
                f"播放 {resp.play_count} | 收藏 {resp.sub_count}",
            ],
        )


@playlist
class Radio(BasePlaylist[md.Radio, md.RadioProgramList, md.ProgramBaseInfo, Program]):
    calling = "电台"
    child_calling = Program.calling
    link_types = ("radio",)

    @property
    @override
    def id(self) -> int:
        return self.info.id

    @classmethod
    @override
    async def from_id(cls, arg_id: int) -> Self:
        resp = await get_radio_info(arg_id)
        return cls(resp)

    @override
    async def _extract_resp_content(
        self,
        resp: md.RadioProgramList,
    ) -> list[md.ProgramBaseInfo]:
        return resp.programs

    @override
    async def _extract_total_count(self, resp: md.RadioProgramList) -> int:
        return resp.count

    @override
    async def _do_get_page(self, page: int) -> md.RadioProgramList:
        return await get_radio_programs(self.id, page)

    @override
    async def _build_selection(self, resp: md.ProgramBaseInfo) -> Program:
        return Program(info=resp)

    @override
    async def _build_list_page(
        self,
        resp: Iterable[md.ProgramBaseInfo],
    ) -> ProgramListPage[Self]:
        return ProgramListPage(resp, self)

    @override
    async def get_name(self) -> str:
        return self.info.name

    @override
    async def get_creators(self) -> list[str]:
        return [self.info.dj.nickname]

    @override
    async def get_cover_url(self) -> str:
        return self.info.pic_url

    @override
    @classmethod
    async def format_description(cls, info: PlaylistInfo) -> str:
        if not cls.is_info_from_cls(info):
            raise TypeError("Info is not from this class")
        base_desc = await super().format_description(info)
        self = info.father
        sec_category = f"/{c}" if (c := self.info.second_category) else ""
        lst_desc = f"\n{cut_string(d)}" if (d := self.info.desc) else ""
        return (
            f"{base_desc}\n"
            f"分类：{self.info.category}{sec_category}\n"
            f"播放 {self.info.play_count} | "
            f"收藏 {self.info.sub_count} | "
            f"点赞 {self.info.liked_count} | "
            f"评论 {self.info.comment_count} | "
            f"分享 {self.info.share_count}"
            f"{lst_desc}"
        )


@searcher
class RadioSearcher(BaseSearcher[md.RadioSearchResult, md.RadioBaseInfo, Radio]):
    child_calling = Radio.calling
    commands = ("网易电台", "wydt", "wydj")

    @override
    @staticmethod
    async def search_from_id(arg_id: int) -> Optional[Radio]:
        with suppress(Exception):
            return await Radio.from_id(arg_id)
        return None

    @override
    async def _extract_resp_content(
        self,
        resp: md.RadioSearchResult,
    ) -> Optional[list[md.RadioBaseInfo]]:
        return [x.base_info for x in resp.resources] if resp.resources else None

    @override
    async def _extract_total_count(self, resp: md.RadioSearchResult) -> int:
        return resp.total_count

    @override
    async def _do_get_page(self, page: int) -> md.RadioSearchResult:
        return await search_radio(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.RadioBaseInfo) -> Radio:
        return await Radio.from_id(resp.id)

    @override
    async def _build_list_page(
        self,
        resp: Iterable[md.RadioBaseInfo],
    ) -> RadioListPage[Self]:
        return RadioListPage(resp, self)
