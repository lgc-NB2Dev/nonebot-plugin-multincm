from typing import List, Optional

from ..config import config
from ..const import MUSIC_LINK_TEMPLATE
from ..data_source import get_track_audio, get_voice_info, search_voice
from ..draw import Table, TableHead, TablePage
from ..types import VoiceBaseInfo, VoiceResource, VoiceSearchResult
from ..utils import format_time
from .base import BaseSearcher, BaseSong, searcher, song

CALLING = "节目"
LINK_TYPES = ["dj", "program"]
COMMANDS = ["电台", "声音", "网易电台", "wydt", "wydj"]


@song
class Voice(BaseSong[VoiceBaseInfo]):
    calling = CALLING
    link_types = LINK_TYPES

    @property
    def song_id(self) -> int:
        return self.info.id

    @classmethod
    async def from_id(cls, program_id: int) -> "Voice":
        info = await get_voice_info(program_id)
        if not info:
            raise ValueError("Voice not found")
        return cls(info)

    async def get_url(self) -> str:
        return MUSIC_LINK_TEMPLATE.format(type=LINK_TYPES[0], id=self.info.id)

    async def get_playable_url(self) -> str:
        song_id = self.info.mainTrackId
        info = (await get_track_audio([song_id]))[0]
        return info.url

    async def get_name(self) -> str:
        return self.info.name

    async def get_artists(self) -> List[str]:
        return [self.info.radio.name]

    async def get_cover_url(self) -> str:
        return self.info.coverUrl

    async def get_lyric(self) -> Optional[str]:
        return None


@searcher
class VoiceSearcher(BaseSearcher[VoiceSearchResult, VoiceResource, Voice]):
    calling = CALLING
    commands = COMMANDS

    @classmethod
    async def from_id(cls, arg_id: int) -> Optional[Voice]:
        try:
            return await Voice.from_id(arg_id)
        except ValueError:
            return None

    async def _build_list_resp(
        self,
        resp: VoiceSearchResult,
        page: int,
    ) -> TablePage:
        if not resp.resources:
            raise ValueError("No resource in raw response")
        table = Table(
            [
                TableHead("序号", align="right"),
                TableHead("节目", max_width=config.ncm_max_name_len),
                TableHead("电台", max_width=config.ncm_max_name_len),
                TableHead("台主", max_width=config.ncm_max_artist_len),
                TableHead("时长", align="center"),
            ],
            [
                [
                    f"[b]{i}[/b]",
                    x.baseInfo.name,
                    x.baseInfo.radio.name,
                    x.baseInfo.dj.nickname,
                    format_time(x.baseInfo.duration),
                ]
                for i, x in enumerate(resp.resources, self._calc_index_offset(page))
            ],
        )
        return TablePage(table, self.child_calling, page, resp.totalCount)

    async def _extract_resp_content(
        self,
        resp: VoiceSearchResult,
    ) -> Optional[List[VoiceResource]]:
        return resp.resources

    async def _do_get_page(self, page: int) -> VoiceSearchResult:
        return await search_voice(self.keyword, page=page)

    async def _build_selection(self, resp: VoiceResource) -> Voice:
        return Voice(info=resp.baseInfo)
