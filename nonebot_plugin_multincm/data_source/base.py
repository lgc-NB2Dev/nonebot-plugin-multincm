import asyncio
from abc import ABC, abstractmethod
from collections.abc import Iterable
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, ClassVar, Generic, Optional, TypeVar, Union
from typing_extensions import Self, TypeAlias, TypeGuard, override

from yarl import URL

from ..config import config
from ..utils import (
    NCMLrcGroupLine,
    build_item_link,
    calc_max_page,
    calc_min_index,
    calc_page_number,
    format_alias,
    format_time,
)
from .raw import md

SongListInnerResp: TypeAlias = Union[
    md.Song,
    md.ProgramBaseInfo,
    md.BasePlaylist,
    md.RadioBaseInfo,
    md.Album,
]

_TRawInfo = TypeVar("_TRawInfo")
_TRawResp = TypeVar("_TRawResp")
_TRawRespInner = TypeVar("_TRawRespInner", bound=SongListInnerResp)
_TSong = TypeVar("_TSong", bound="BaseSong")
_TSongList = TypeVar("_TSongList", bound="BaseSongList")
_TPlaylist = TypeVar("_TPlaylist", bound="BasePlaylist")
_TSearcher = TypeVar("_TSearcher", bound="BaseSearcher")
_TSongOrList = TypeVar("_TSongOrList", bound=Union["BaseSong", "BaseSongList"])
_TResolvable = TypeVar("_TResolvable", bound="BaseResolvable")


registered_resolvable: dict[str, type["BaseResolvable"]] = {}
registered_song: set[type["BaseSong"]] = set()
registered_playlist: set[type["BasePlaylist"]] = set()
registered_searcher: dict[type["BaseSearcher"], tuple[str, ...]] = {}


class ResolvableFromID(ABC):
    link_types: ClassVar[tuple[str, ...]]

    @property
    @abstractmethod
    def id(self) -> int: ...

    @classmethod
    @abstractmethod
    async def from_id(cls, arg_id: int) -> Self: ...

    async def get_url(self) -> str:
        if not self.link_types:
            raise ValueError("No link types found")
        return build_item_link(self.link_types[0], self.id)


def link_resolvable(cls: type[_TResolvable]):
    if n := next((x for x in cls.link_types if x in registered_resolvable), None):
        raise ValueError(f"Duplicate link type: {n}")
    registered_resolvable.update(dict.fromkeys(cls.link_types, cls))
    return cls


def song(cls: type[_TSong]):
    registered_song.add(cls)
    return link_resolvable(cls)


def playlist(cls: type[_TPlaylist]):
    registered_playlist.add(cls)
    return link_resolvable(cls)


def searcher(cls: type[_TSearcher]):
    registered_searcher[cls] = cls.commands
    return cls


async def resolve_from_link_params(
    link_type: str,
    link_id: int,
) -> "GeneralSongOrPlaylist":
    item_class = registered_resolvable.get(link_type)
    if not item_class:
        raise ValueError(f"Non-resolvable link type: {link_type}")
    return await item_class.from_id(link_id)


@dataclass
class SongInfo(Generic[_TSong]):
    father: _TSong
    name: str
    alias: Optional[list[str]]
    artists: list[str]
    duration: int
    url: str
    cover_url: str
    playable_url: str

    @property
    def id(self) -> int:
        return self.father.id

    @property
    def display_artists(self) -> str:
        return "、".join(self.artists)

    @property
    def display_name(self) -> str:
        return format_alias(self.name, self.alias)

    @property
    def display_duration(self) -> str:
        return format_time(self.duration)

    @property
    def file_suffix(self) -> Optional[str]:
        return URL(self.playable_url).suffix.removeprefix(".") or None

    @property
    def display_filename(self) -> str:
        return (
            f"{self.display_name} - {self.display_artists}.{self.file_suffix or 'mp3'}"
        )

    @property
    def download_filename(self) -> str:
        return f"{type(self.father).__name__}_{self.id}.{self.file_suffix or 'mp3'}"

    async def get_description(self) -> str:
        return await self.father.format_description(self)


class BaseSong(ResolvableFromID, ABC, Generic[_TRawResp]):
    calling: ClassVar[str]

    def __init__(self, info: _TRawResp) -> None:
        self.info: _TRawResp = info

    def __str__(self) -> str:
        return f"{type(self).__name__}(id={self.id})"

    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, type(self)) and value.id == self.id

    @property
    @abstractmethod
    @override
    def id(self) -> int: ...

    @classmethod
    @abstractmethod
    @override
    async def from_id(cls, arg_id: int) -> Self: ...

    @abstractmethod
    async def get_name(self) -> str: ...

    @abstractmethod
    async def get_alias(self) -> Optional[list[str]]: ...

    @abstractmethod
    async def get_artists(self) -> list[str]: ...

    @abstractmethod
    async def get_duration(self) -> int: ...

    @abstractmethod
    async def get_cover_url(self) -> str: ...

    @abstractmethod
    async def get_playable_url(self) -> str: ...

    @abstractmethod
    async def get_lyrics(self) -> Optional[list[NCMLrcGroupLine]]: ...

    async def get_info(self) -> SongInfo:
        (
            (name, alias, artists, duration, url, cover_url),
            (playable_url,),
        ) = await asyncio.gather(  # treat type checker
            asyncio.gather(
                self.get_name(),
                self.get_alias(),
                self.get_artists(),
                self.get_duration(),
                self.get_url(),
                self.get_cover_url(),
            ),
            asyncio.gather(
                self.get_playable_url(),
            ),
        )
        return SongInfo(
            father=self,
            name=name,
            alias=alias,
            artists=artists,
            duration=duration,
            url=url,
            cover_url=cover_url,
            playable_url=playable_url,
        )

    @classmethod
    def is_info_from_cls(cls, info: SongInfo) -> TypeGuard[SongInfo[Self]]:
        return isinstance(info.father, cls)

    @classmethod
    async def format_description(cls, info: SongInfo) -> str:
        # if not cls.is_info_from_cls(info):
        #     raise TypeError("Info is not from this class")
        alias = format_alias("", info.alias) if info.alias else ""
        return f"{info.name}{alias}\nBy：{info.display_artists}\n时长 {info.display_duration}"


@dataclass
class ListPageCard:
    cover: str
    title: str
    alias: str = ""
    extras: list[str] = field(default_factory=list)
    small_extras: list[str] = field(default_factory=list)


@dataclass
class BaseSongListPage(Generic[_TRawRespInner, _TSongList]):
    content: Iterable[_TRawRespInner]
    father: _TSongList

    @override
    def __str__(self) -> str:
        return f"{type(self).__name__}(father={self.father})"

    @classmethod
    @abstractmethod
    async def transform_resp_to_list_card(
        cls,
        resp: _TRawRespInner,
    ) -> ListPageCard: ...

    async def transform_to_list_cards(self) -> list[ListPageCard]:
        return await asyncio.gather(
            *[self.transform_resp_to_list_card(resp) for resp in self.content],
        )


class BaseSongList(ABC, Generic[_TRawResp, _TRawRespInner, _TSongOrList]):
    child_calling: ClassVar[str]

    def __init__(self) -> None:
        self.current_page: int = 1
        self._total_count: Optional[int] = None
        self._cache: dict[int, _TRawRespInner] = {}

    def __str__(self) -> str:
        return (
            f"{type(self).__name__}"
            f"(current_page={self.current_page}, total_count={self._total_count})"
        )

    @abstractmethod
    def __eq__(self, value: object, /) -> bool: ...

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
    ) -> Optional[list[_TRawRespInner]]: ...

    @abstractmethod
    async def _extract_total_count(self, resp: _TRawResp) -> int: ...

    @abstractmethod
    async def _do_get_page(self, page: int) -> _TRawResp: ...

    @abstractmethod
    async def _build_selection(self, resp: _TRawRespInner) -> _TSongOrList: ...

    @abstractmethod
    async def _build_list_page(
        self,
        resp: Iterable[_TRawRespInner],
    ) -> BaseSongListPage[_TRawRespInner, Self]: ...

    def _update_cache(self, page: int, data: list[_TRawRespInner]):
        min_index = calc_min_index(page)
        self._cache.update({min_index + i: item for i, item in enumerate(data)})

    def page_valid(self, page: int) -> bool:
        return 1 <= page <= self.max_page

    def index_valid(self, index: int) -> bool:
        return 0 <= index < self.total_count

    async def get_page(
        self,
        page: Optional[int] = None,
    ) -> Union[BaseSongListPage[_TRawRespInner, Self], _TSongOrList, None]:
        if page is None:
            page = self.current_page
        if not ((not self._total_count) or self.page_valid(page)):
            raise ValueError("Page out of range")

        min_index = calc_min_index(page)
        max_index = min_index + config.ncm_list_limit
        index_range = range(min_index, max_index + 1)
        if all(page in self._cache for page in index_range):
            return await self._build_list_page(
                self._cache[page] for page in index_range
            )

        resp = await self._do_get_page(page)
        content = await self._extract_resp_content(resp)
        self._total_count = await self._extract_total_count(resp)
        self.current_page = page
        if content is None:
            return None
        if len(content) == 1:
            return await self._build_selection(content[0])

        self._cache.update({min_index + i: item for i, item in enumerate(content)})
        return await self._build_list_page(content)

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
            min_index = calc_min_index(page_num)
            content = resp[index - min_index]
        return await self._build_selection(content)


@dataclass
class PlaylistInfo(Generic[_TPlaylist]):
    father: _TPlaylist
    name: str
    creators: list[str]
    url: str
    cover_url: str

    @property
    def id(self) -> int:
        return self.father.id

    @property
    def display_creators(self) -> str:
        return "、".join(self.creators)

    async def get_description(self) -> str:
        return await self.father.format_description(self)


class BasePlaylist(
    ResolvableFromID,
    BaseSongList[_TRawResp, _TRawRespInner, _TSongOrList],
    Generic[_TRawInfo, _TRawResp, _TRawRespInner, _TSongOrList],
):
    calling: ClassVar[str]

    @override
    def __init__(self, info: _TRawInfo) -> None:
        super().__init__()
        self.info: _TRawInfo = info

    @override
    def __str__(self) -> str:
        return f"{super().__str__()[:-1]}, id={self.id})"

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, type(self)) and value.id == self.id

    @property
    @abstractmethod
    @override
    def id(self) -> int: ...

    @classmethod
    @abstractmethod
    @override
    async def from_id(cls, arg_id: int) -> Self: ...

    @abstractmethod
    async def get_name(self) -> str: ...

    @abstractmethod
    async def get_creators(self) -> list[str]: ...

    @abstractmethod
    async def get_cover_url(self) -> str: ...

    async def get_info(self) -> PlaylistInfo:
        name, creators, url, cover_url = await asyncio.gather(
            self.get_name(),
            self.get_creators(),
            self.get_url(),
            self.get_cover_url(),
        )
        return PlaylistInfo(
            father=self,
            name=name,
            creators=creators,
            url=url,
            cover_url=cover_url,
        )

    @classmethod
    def is_info_from_cls(
        cls,
        info: PlaylistInfo,
    ) -> TypeGuard[PlaylistInfo[Self]]:
        return isinstance(info.father, cls)

    @classmethod
    async def format_description(cls, info: PlaylistInfo) -> str:
        # if not cls.is_info_from_cls(info):
        #     raise TypeError("Info is not from this class")
        return f"{info.father.calling}：{info.name}\nBy: {info.display_creators}"


class BaseSearcher(BaseSongList[_TRawResp, _TRawRespInner, _TSongOrList]):
    commands: tuple[str, ...]

    @override
    def __init__(self, keyword: str) -> None:
        super().__init__()
        self.keyword: str = keyword

    @override
    def __str__(self) -> str:
        return f"{super().__str__()[:-1]}, keyword={self.keyword})"

    @override
    def __eq__(self, value: object, /) -> bool:
        return isinstance(value, type(self)) and value.keyword == self.keyword

    @staticmethod
    @abstractmethod
    async def search_from_id(arg_id: int) -> Optional[_TSongOrList]: ...

    @override
    async def get_page(
        self,
        page: Optional[int] = None,
    ) -> Union[BaseSongListPage[_TRawRespInner, Self], _TSongOrList, None]:
        if self.keyword.isdigit():
            with suppress(Exception):
                if song := await self.search_from_id(int(self.keyword)):
                    return song
        return await super().get_page(page)


BaseResolvable: TypeAlias = Union[BaseSong, BasePlaylist]

GeneralSong: TypeAlias = BaseSong[Any]
GeneralSongOrList: TypeAlias = Union[
    GeneralSong,
    BaseSongList[Any, SongListInnerResp, "GeneralSongOrList"],
]
GeneralSongList: TypeAlias = BaseSongList[Any, SongListInnerResp, GeneralSongOrList]
GeneralPlaylist: TypeAlias = BasePlaylist[Any, Any, SongListInnerResp, GeneralSong]
GeneralSearcher: TypeAlias = BaseSearcher[Any, SongListInnerResp, GeneralSongOrList]
GeneralSongListPage: TypeAlias = BaseSongListPage[SongListInnerResp, GeneralSongList]
GeneralSongOrPlaylist: TypeAlias = Union[GeneralSong, GeneralPlaylist]
# GeneralResolvable: TypeAlias = GeneralSongOrPlaylist

GeneralGetPageReturn: TypeAlias = Union[
    BaseSongListPage[SongListInnerResp, GeneralSongList],
    GeneralSongOrList,
    None,
]
GeneralSongInfo: TypeAlias = SongInfo[GeneralSong]
GeneralPlaylistInfo: TypeAlias = PlaylistInfo[GeneralPlaylist]
