from typing import List

from .utils import jinja_env, render_html


async def render_lyrics(groups: List[List[str]]) -> bytes:
    return await render_html(
        jinja_env.get_template("lyrics.html.jinja").render(groups=groups),
    )
