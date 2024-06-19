from abc import abstractmethod
from contextlib import suppress
from typing import ClassVar, Dict, Generic, List, Optional, TypeVar, Union
from typing_extensions import Any, Self, TypeAlias, override

from ..config import config
from ..data_source import md
from ..utils import calc_max_page, calc_min_index, calc_page_number

SongListInnerResp: TypeAlias = Union[md.Song, md.VoiceResource, md.PlaylistFromSearch]

_TRawResp = TypeVar("_TRawResp")
_TRawRespInner = TypeVar("_TRawRespInner", bound=SongListInnerResp)
_TSong = TypeVar("_TSong", bound="BaseSong")
_TSongOrList = TypeVar("_TSongOrList", bound=Union["BaseSong", "BaseSongList"])


class BaseSong(Generic[_TRawResp]):
    calling: ClassVar[str] = "BaseSong"

    def __init__(self, info: _TRawResp) -> None:
        self.info: _TRawResp = info

    @property
    @abstractmethod
    def id(self) -> int: ...

    @classmethod
    @abstractmethod
    async def from_id(cls, arg_id: int) -> Self: ...

    @abstractmethod
    async def get_url(self) -> str: ...

    @abstractmethod
    async def get_playable_url(self) -> str: ...

    @abstractmethod
    async def get_name(self) -> str: ...

    @abstractmethod
    async def get_artists(self) -> List[str]: ...

    @abstractmethod
    async def get_cover_url(self) -> str: ...

    @abstractmethod
    async def get_lyric(self) -> Optional[str]: ...


class BaseSongList(Generic[_TRawResp, _TRawRespInner, _TSongOrList]):
    child_calling: ClassVar[str] = "BaseSongList"

    def __init__(self) -> None:
        self.current_page: int = 1
        self._total_count: Optional[int] = None
        self._cache: Dict[int, _TRawRespInner] = {}

    @property
    def total_count(self) -> int:
        if self._total_count is None:
            raise ValueError("Total count not set, please call get_page first")
        return self._total_count

    @property
    def max_page(self) -> int:
        return calc_max_page(self.total_count)

    @property
    def is_first_page(self) -> bool:
        return self.current_page == 1

    @property
    def is_last_page(self) -> bool:
        return self.current_page == self.max_page

    @abstractmethod
    async def _extract_resp_content(
        self,
        resp: _TRawResp,
    ) -> Optional[List[_TRawRespInner]]: ...

    @abstractmethod
    async def _extract_total_count(self, resp: _TRawResp) -> int: ...

    @abstractmethod
    async def _do_get_page(self, page: int) -> _TRawResp: ...

    @abstractmethod
    async def _build_selection(self, resp: _TRawRespInner) -> _TSongOrList: ...

    def _update_cache(self, page: int, data: List[_TRawRespInner]):
        min_index = calc_min_index(page)
        self._cache.update({min_index + i: item for i, item in enumerate(data)})

    def page_valid(self, page: int) -> bool:
        return 1 <= page <= self.max_page

    def index_valid(self, index: int) -> bool:
        return 0 <= index < self.total_count

    async def get_page(
        self,
        page: Optional[int] = None,
    ) -> Union[List[_TRawRespInner], _TSongOrList, None]:
        if page is None:
            page = self.current_page
        if not ((not self._total_count) or self.page_valid(page)):
            raise ValueError("Page out of range")

        min_index = calc_min_index(page)
        max_index = min_index + config.ncm_list_limit
        index_range = range(min_index, max_index + 1)
        if all(page in self._cache for page in index_range):
            return [self._cache[page] for page in index_range]

        resp = await self._do_get_page(page)
        content = await self._extract_resp_content(resp)
        self._total_count = await self._extract_total_count(resp)
        self.current_page = page
        if content is None:
            return None
        if len(content) == 1:
            return await self._build_selection(content[0])

        self._cache.update({min_index + i: item for i, item in enumerate(content)})
        return content

    async def select(self, index: int) -> _TSongOrList:
        page_num = calc_page_number(index)
        if index in self._cache:
            content = self._cache[index]
        elif not (1 <= page_num <= self.max_page):
            raise ValueError("Index out of range")
        else:
            resp = await self._extract_resp_content(await self._do_get_page(page_num))
            if resp is None:
                raise ValueError("Empty response, index may out of range")
            self._update_cache(page_num, resp)
            content = resp[0]
        return await self._build_selection(content)


class BasePlaylist(BaseSongList[_TRawResp, _TRawRespInner, _TSong]):
    @override
    def __init__(self, info: _TRawResp) -> None:
        super().__init__()
        self.info: _TRawResp = info

    @property
    @abstractmethod
    def id(self) -> int: ...

    @classmethod
    @abstractmethod
    async def from_id(cls, arg_id: int) -> Self: ...

    @abstractmethod
    async def get_url(self) -> str: ...


class BaseSearcher(BaseSongList[_TRawResp, _TRawRespInner, _TSongOrList]):
    @override
    def __init__(self, keyword: str) -> None:
        super().__init__()
        self.keyword: str = keyword

    @staticmethod
    @abstractmethod
    async def search_from_id(arg_id: int) -> Optional[_TSongOrList]: ...

    @override
    async def get_page(
        self,
        page: Optional[int] = None,
    ) -> Union[List[_TRawRespInner], _TSongOrList, None]:
        if self.keyword.isdigit():
            with suppress(Exception):
                if song := await self.search_from_id(int(self.keyword)):
                    return song
        return await super().get_page(page)


GeneralSong: TypeAlias = BaseSong[Any]
GeneralSongOrList: TypeAlias = Union[
    GeneralSong,
    BaseSongList[Any, SongListInnerResp, "GeneralSongOrList"],
]
GeneralSongList: TypeAlias = BaseSongList[Any, SongListInnerResp, GeneralSongOrList]
GeneralPlaylist: TypeAlias = BasePlaylist[Any, SongListInnerResp, GeneralSong]
GeneralSearcher: TypeAlias = BaseSearcher[Any, SongListInnerResp, GeneralSongOrList]
