from typing import List, Optional
from typing_extensions import Self, override

from .base import BaseSearcher, BaseSong, searcher, song
from .raw import get_track_audio, get_voice_info, md, search_voice


@song
class Voice(BaseSong[md.VoiceBaseInfo]):
    calling = "声音"
    link_types = ("program", "dj")

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
    async def get_name(self) -> str:
        return self.info.name

    @override
    async def get_alias(self) -> Optional[List[str]]:
        return None

    @override
    async def get_artists(self) -> List[str]:
        return [self.info.radio.name]

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


@searcher
class VoiceSearcher(BaseSearcher[md.VoiceSearchResult, md.VoiceResource, Voice]):
    child_calling = "声音"
    commands = ("网易声音", "wysy", "wyvo")

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
