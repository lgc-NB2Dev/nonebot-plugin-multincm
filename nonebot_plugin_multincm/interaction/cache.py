from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, Tuple, Type, TypeVar, Union
from typing_extensions import Self, TypeAlias, override

from cachetools import TTLCache
from cookit.loguru import logged_suppress
from nonebot.adapters import Event as BaseEvent
from nonebot.matcher import current_event

from ..config import config
from ..data_source import BasePlaylist, BaseSong, ResolvableFromID

CacheableItemType: TypeAlias = Union[BaseSong, BasePlaylist]
CacheItemType: TypeAlias = "IDCache"

TC = TypeVar("TC", bound=CacheableItemType)
TID = TypeVar("TID", bound=ResolvableFromID)


class BaseCache(ABC, Generic[TC]):
    @classmethod
    @abstractmethod
    async def build(cls, item: TC) -> Self: ...

    @abstractmethod
    async def restore(self) -> TC: ...


@dataclass
class IDCache(BaseCache, Generic[TID]):
    id: int
    original: Type[TID]

    @override
    @classmethod
    async def build(cls, item: TID) -> Self:
        return cls(id=item.id, original=type(item))

    @override
    async def restore(self) -> TID:
        return await self.original.from_id(self.id)


cache: TTLCache[str, CacheItemType] = TTLCache(
    config.ncm_msg_cache_size,
    config.ncm_msg_cache_time,
)


async def set_cache(item: CacheableItemType, event: Optional[BaseEvent] = None):
    if not event:
        event = current_event.get()
    session = event.get_session_id()
    with logged_suppress(f"Failed to set cache for session {session}"):
        cache[session] = await IDCache.build(item)


async def get_cache(
    event: Optional[BaseEvent] = None,
    expected_type: Optional[
        Union[Type[ResolvableFromID], Tuple[Type[ResolvableFromID], ...]]
    ] = None,
) -> Optional[CacheableItemType]:
    if not event:
        event = current_event.get()

    session = event.get_session_id()
    cache_item = cache.get(session)
    if (not cache_item) or (
        expected_type
        and (
            (not isinstance(cache_item, IDCache))
            or (not issubclass(cache_item.original, expected_type))
        )
    ):
        return None

    with logged_suppress(f"Failed to get cache for session {session}"):
        return await cache_item.restore()
