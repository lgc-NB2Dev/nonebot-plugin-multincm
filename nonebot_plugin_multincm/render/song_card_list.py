from dataclasses import dataclass
from typing import List

from .utils import jinja_env, render_html


@dataclass
class CardItem:
    title: str
    cover: str
    author: str
    info: str


async def render_card_list(
    title: str,
    items: List[CardItem],
    page_current: int,
    page_max: int,
    index_offset: int = 0,
) -> bytes:
    return await render_html(
        jinja_env.get_template("card_list.html.jinja").render(
            title=title,
            items=items,
            page_current=page_current,
            page_max=page_max,
            index_offset=index_offset,
        ),
    )
