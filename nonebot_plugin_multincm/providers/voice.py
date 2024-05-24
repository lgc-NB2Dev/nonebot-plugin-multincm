from typing import List, Optional
from typing_extensions import Self, override

from ..data_source import (
    MUSIC_LINK_TEMPLATE,
    get_track_audio,
    get_voice_info,
    md,
    search_voice,
)
from .base import BaseSearcher, BaseSong


class Voice(BaseSong[md.VoiceBaseInfo]):
    @property
    @override
    def id(self) -> int:
        return self.info.id

    @classmethod
    @override
    async def from_id(cls, arg_id: int) -> Self:
        info = await get_voice_info(arg_id)
        if not info:
            raise ValueError("Voice not found")
        return cls(info)

    @override
    async def get_url(self) -> str:
        return MUSIC_LINK_TEMPLATE.format(type="dj", id=self.info.id)

    @override
    async def get_playable_url(self) -> str:
        song_id = self.info.main_track_id
        info = (await get_track_audio([song_id]))[0]
        return info.url

    @override
    async def get_name(self) -> str:
        return self.info.name

    @override
    async def get_artists(self) -> List[str]:
        return [self.info.radio.name]

    @override
    async def get_cover_url(self) -> str:
        return self.info.cover_url

    @override
    async def get_lyric(self) -> Optional[str]:
        return None


class VoiceSearcher(BaseSearcher[md.VoiceSearchResult, md.VoiceResource, Voice]):
    @staticmethod
    @override
    async def search_from_id(arg_id: int) -> Optional[Voice]:
        try:
            return await Voice.from_id(arg_id)
        except ValueError:
            return None

    @override
    async def _extract_resp_content(
        self,
        resp: md.VoiceSearchResult,
    ) -> Optional[List[md.VoiceResource]]:
        return resp.resources

    @override
    async def _extract_total_count(self, resp: md.VoiceSearchResult) -> int:
        return resp.total_count

    @override
    async def _do_get_page(self, page: int) -> md.VoiceSearchResult:
        return await search_voice(self.keyword, page=page)

    @override
    async def _build_selection(self, resp: md.VoiceResource) -> Voice:
        return Voice(info=resp.base_info)
