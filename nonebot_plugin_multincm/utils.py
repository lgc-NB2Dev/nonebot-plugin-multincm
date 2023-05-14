import asyncio
from functools import partial, wraps
from typing import Awaitable, Callable, TypeVar

from typing_extensions import ParamSpec

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
