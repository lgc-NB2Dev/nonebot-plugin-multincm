from typing import List, TypedDict

from .utils import render_html, render_template


class LyricsRenderParams(TypedDict):
    groups: List[List[str]]


async def render_lyrics(**kwargs: LyricsRenderParams) -> bytes:
    return await render_html(await render_template("lyrics.html.jinja", **kwargs))
