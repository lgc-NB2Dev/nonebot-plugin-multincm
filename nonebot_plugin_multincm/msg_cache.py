import time
from typing import (
    Dict,
    Generic,
    Iterable,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    overload,
)

from .config import config
from .providers import BaseSong

KT = TypeVar("KT")
VT = TypeVar("VT")


class SongCache(NamedTuple):
    song_class: Type[BaseSong]
    song_id: int

    async def get(self) -> BaseSong:
        return await self.song_class.from_id(self.song_id)


# “优雅”
class CacheManager(Generic[KT, VT], Dict[KT, Tuple[float, VT]]):
    def __init__(self, *args, **kwargs):
        # self._job = scheduler.add_job(self.clear_expired, "interval", minutes=1)
        super().__init__(*args, **kwargs)

    # def __del__(self):
    # scheduler.remove_job(self._job)

    def __getitem__(self, __key: KT) -> VT:
        self.clear_expired()
        return super().__getitem__(__key)[1]

    @overload
    def get(
        self,
        __key: KT,
        __default: Literal[None] = None,  # noqa: RUF013
    ) -> Optional[VT]:
        ...

    @overload
    def get(self, __key: KT, __default: VT = ...) -> VT:
        ...

    def get(self, __key, __default=None):
        self.clear_expired()
        it = super().get(__key)
        return it[1] if it else __default

    def __setitem__(self, __key: KT, __value: VT):
        self.clear_expired()
        return super().__setitem__(__key, (time.time(), __value))

    def set(self, __key: KT, __value: VT):  # noqa: A003
        return self.__setitem__(__key, __value)

    def values(self) -> Iterable[VT]:
        self.clear_expired()
        for v in super().values():
            yield v[1]

    def items(self) -> Iterable[Tuple[KT, VT]]:
        self.clear_expired()
        for k, v in super().items():
            yield k, v[1]

    @overload
    def pop(
        self,
        __key: KT,
        __default: Literal[None] = None,  # noqa: RUF013
    ) -> Optional[VT]:
        ...

    @overload
    def pop(self, __key: KT, __default: VT = ...) -> VT:
        ...

    def pop(self, __key, __default=None):
        self.clear_expired()
        try:
            return super().pop(__key)[1]
        except KeyError:
            return __default

    def clear_expired(self):
        now_t = time.time()
        for k, (create_t, _) in self.copy().items():
            if now_t - create_t >= config.ncm_msg_cache_time:
                del self[k]


# song_msg_id_cache: CacheManager[int, SongCache] = CacheManager()
chat_last_song_cache: CacheManager[str, SongCache] = CacheManager()
