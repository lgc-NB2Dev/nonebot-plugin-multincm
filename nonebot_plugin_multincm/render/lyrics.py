from typing import List, TypedDict
from typing_extensions import Unpack

from .utils import render_html, render_template


class LyricsRenderParams(TypedDict):
    groups: List[List[str]]


async def render_lyrics(**kwargs: Unpack[LyricsRenderParams]) -> bytes:
    return await render_html(await render_template("lyrics.html.jinja", **kwargs))
