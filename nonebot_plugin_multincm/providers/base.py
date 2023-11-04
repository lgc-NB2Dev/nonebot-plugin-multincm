import asyncio
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import (
    Any,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)
from typing_extensions import Self

from nonebot.adapters.onebot.v11 import Message, MessageSegment

from ..config import config
from ..draw import SearchResp
from ..types import SearchRespModelType, SongInfoModelType

_TSongInfoModel = TypeVar("_TSongInfoModel", bound=SongInfoModelType)
_TRawSearchResp = TypeVar("_TRawSearchResp", bound=SearchRespModelType)
_T_RawRespContent = TypeVar("_T_RawRespContent")

_TBaseSong = TypeVar("_TBaseSong", bound="BaseSong")
_TBasePlaylist = TypeVar("_TBasePlaylist", bound="BasePlaylist")
_TBaseSongOrPlaylist = TypeVar("_TBaseSongOrPlaylist", "BaseSong", "BasePlaylist")
_TSearcher = TypeVar("_TSearcher", bound="BaseSearcher")


class BaseSong(ABC, Generic[_TSongInfoModel]):
    calling: str = "BaseSong"
    link_types: ClassVar[List[str]] = []

    info: _TSongInfoModel

    def __init__(self, info: _TSongInfoModel, *_, **__) -> None:
        self.info = info

    @abstractmethod
    async def get_id(self) -> int:
        ...

    @classmethod
    @abstractmethod
    async def from_id(cls, song_id: int) -> Self:
        ...

    @abstractmethod
    async def get_url(self) -> str:
        ...

    @abstractmethod
    async def get_playable_url(self) -> str:
        ...

    @abstractmethod
    async def get_name(self) -> str:
        ...

    @abstractmethod
    async def get_artists(self) -> List[str]:
        ...

    @abstractmethod
    async def get_cover_url(self) -> str:
        ...

    @abstractmethod
    async def get_lyric(self) -> Optional[str]:
        ...

    async def to_card_message(self) -> Message:
        url, playable_url, name, artists, cover_url = await asyncio.gather(
            self.get_url(),
            self.get_playable_url(),
            self.get_name(),
            self.get_artists(),
            self.get_cover_url(),
        )
        seg = MessageSegment(
            "music",
            {
                "type": "custom",
                "subtype": "163",
                "url": url,
                "jumpUrl": url,  # icqq
                "voice": playable_url,
                "title": name,
                "content": "、".join(artists),
                "image": cover_url,
            },
        )
        return Message(seg)


class BasePlaylist(
    ABC,
    Generic[_TRawSearchResp, _T_RawRespContent, _TBaseSongOrPlaylist],
):
    calling: str = "BasePlaylist"
    child_calling: str = "BaseSong"
    link_types: ClassVar[List[str]] = []

    _last_page: int
    _last_resp: Optional[SearchResp]
    _cache: Dict[int, _TRawSearchResp]

    @property
    def last_page(self) -> int:
        return self._last_page

    @property
    def last_resp(self) -> Optional[SearchResp]:
        return self._last_resp

    def __init__(self, *_, **__) -> None:
        self._last_page = 1
        self._last_resp = None
        self._cache = {}

    @abstractmethod
    async def _build_list_resp(self, resp: _TRawSearchResp, page: int) -> SearchResp:
        ...

    @abstractmethod
    async def _extract_resp_content(
        self,
        resp: _TRawSearchResp,
    ) -> Optional[List[_T_RawRespContent]]:
        ...

    @abstractmethod
    async def _do_get_page(self, page: int) -> _TRawSearchResp:
        ...

    @abstractmethod
    async def _build_selection(
        self,
        resp: _T_RawRespContent,
    ) -> _TBaseSongOrPlaylist:
        ...

    @classmethod
    @abstractmethod
    async def from_id(cls, arg_id: int) -> Self:
        ...

    def _calc_index_offset(self, page: int) -> int:
        return ((page - 1) * config.ncm_list_limit) + 1

    async def get_page(
        self,
        page: int = 1,
    ) -> Union[SearchResp, _TBaseSongOrPlaylist, None]:
        raw_resp = (
            self._cache[page] if page in self._cache else await self._do_get_page(page)
        )
        extracted = await self._extract_resp_content(raw_resp)
        if not extracted:
            return None
        if page == 1 and len(extracted) == 1:
            return await self._build_selection(extracted[0])

        resp = await self._build_list_resp(raw_resp, page)
        if isinstance(resp, SearchResp):
            self._last_page = page
            self._last_resp = resp
            self._cache[page] = raw_resp
        return resp

    async def next_page(self) -> SearchResp:
        if not self._last_resp:
            raise ValueError("Please do a search first")
        if self._last_page >= self._last_resp.max_page:
            raise ValueError("Already last page")
        return cast(Any, await self.get_page(self._last_page + 1))

    async def prev_page(self) -> SearchResp:
        if self._last_page <= 1:
            raise ValueError("Already first page")
        return cast(Any, await self.get_page(self._last_page - 1))

    async def select(self, index: int) -> _TBaseSongOrPlaylist:
        index -= 1  # item index starts with 0
        page_index = (index // config.ncm_list_limit) + 1  # page index starts with 1
        if page_index not in self._cache:
            raise ValueError("Cache not found, please do a properly search first")

        caches = await self._extract_resp_content(self._cache[page_index])
        if (not caches) or (
            (item_index := index % config.ncm_list_limit) >= len(caches)
        ):
            raise ValueError("Index out of range")
        return await self._build_selection(caches[item_index])


class BaseSearcher(
    Generic[_TRawSearchResp, _T_RawRespContent, _TBaseSongOrPlaylist],
    BasePlaylist[_TRawSearchResp, _T_RawRespContent, _TBaseSongOrPlaylist],
):
    commands: ClassVar[List[str]] = []

    keyword: str

    def __init__(self, keyword: str, *_, **__) -> None:
        self.keyword = keyword
        super().__init__(*_, **__)

    @classmethod
    async def from_id(cls, arg_id: int) -> Optional[_TBaseSongOrPlaylist]:
        raise NotImplementedError

    async def get_page(
        self,
        page: int = 1,
    ) -> Union[SearchResp, _TBaseSongOrPlaylist, None]:
        if self.keyword.isdigit():
            with suppress(Exception):
                if song := await self.from_id(int(self.keyword)):
                    return song
        return await super().get_page(page)


songs: List[Type[BaseSong]] = []
playlists: List[Type[BasePlaylist]] = []
searchers: List[Type[BaseSearcher]] = []


def song(cls: Type[_TBaseSong]) -> Type[_TBaseSong]:
    songs.append(cls)
    return cls


def playlist(cls: Type[_TBasePlaylist]) -> Type[_TBasePlaylist]:
    playlists.append(cls)
    return cls


def searcher(cls: Type[_TSearcher]) -> Type[_TSearcher]:
    searchers.append(cls)
    return cls
