from typing import TYPE_CHECKING

from .utils import render_html, render_template

if TYPE_CHECKING:
    from ..utils import NCMLrcGroupLine


async def render_lyrics(groups: list["NCMLrcGroupLine"]) -> bytes:
    group_tuples = [[(n, r) for n, r in x.lrc.items()] for x in groups]
    sort_order = ("roma", "main", "trans")
    for group in group_tuples:
        group.sort(key=lambda x: sort_order.index(x[0]) if x[0] in sort_order else 999)
    return await render_html(
        await render_template(
            "lyrics.html.jinja",
            groups=group_tuples,
        ),
    )
