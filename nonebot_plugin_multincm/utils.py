import asyncio
from functools import partial, wraps
from typing import Awaitable, Callable, List, TypeVar

from typing_extensions import ParamSpec

from .types import Artist

P = ParamSpec("P")
TR = TypeVar("TR")


def awaitable(func: Callable[P, TR]) -> Callable[P, Awaitable[TR]]:
    @wraps(func)
    async def run(*args: P.args, **kwargs: P.kwargs):
        return await asyncio.get_event_loop().run_in_executor(
            None,
            partial(func, *args, **kwargs),
        )

    return run


def format_time(time: int) -> str:
    s, _ = divmod(time, 1000)
    m, s = divmod(s, 60)
    return f"{m:0>2d}:{s:0>2d}"


def format_alias(name: str, alias: List[str]) -> str:
    return f'{name}（{"；".join(alias)}）' if alias else name


def format_artists(artists: List[Artist]) -> str:
    return "、".join([format_alias(x.name, x.alias) for x in artists])
