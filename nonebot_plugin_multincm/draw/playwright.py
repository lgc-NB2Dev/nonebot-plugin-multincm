from pathlib import Path
from typing import Optional

import bbcode
from jinja2 import Template
from nonebot import logger
from nonebot_plugin_htmlrender import get_new_page
from pil_utils.fonts import Font
from pil_utils.types import ColorType, HAlignType

from ..config import config
from ..const import RES_DIR
from .shared import TablePage

SONG_LIST_TEMPLATE = Template(
    (RES_DIR / "song_list.html.jinja").read_text(encoding="u8"),
    enable_async=True,
)
LYRIC_TEMPLATE = Template(
    (RES_DIR / "lyric.html.jinja").read_text(encoding="u8"),
    enable_async=True,
)
BBCODE_PARSER = bbcode.Parser()
BBCODE_PARSER.install_default_formatters()


def get_font_path_uri() -> Optional[str]:
    font_path = config.ncm_list_font
    if font_path:
        if (path := Path(font_path)).exists():
            return path.resolve().as_uri()
        return Font.find(font_path).path.as_uri()
    return None


async def render_template(
    template: "Template",
    **kwargs,
) -> bytes:
    html_txt = await template.render_async(**kwargs)
    logger.debug(html_txt)
    async with get_new_page() as page:
        await page.goto(RES_DIR.as_uri())
        await page.set_content(html_txt, wait_until="networkidle")
        main_elem = await page.query_selector(".main")
        assert main_elem
        return await main_elem.screenshot(type="jpeg")


async def draw_table_page(res: TablePage) -> bytes:
    for x in res.table.head:
        x.name = BBCODE_PARSER.format(x.name)
    lines = [[BBCODE_PARSER.format(y) for y in x] for x in res.table.rows]

    return await render_template(
        SONG_LIST_TEMPLATE,
        calling=res.calling,
        current_page=res.current_page,
        max_page=res.max_page,
        max_count=res.max_count,
        heads=res.table.head,
        lines=lines,
        font_path=get_font_path_uri(),
        enumerate=enumerate,
    )


async def str_to_pic(
    txt: str,
    padding: int = 20,
    font_color: ColorType = (241, 246, 249),
    bg_color: ColorType = (33, 42, 62),
    font_size: int = 30,
    text_align: HAlignType = "left",
) -> bytes:
    def color_type_to_css(clr: ColorType) -> str:
        if isinstance(clr, tuple):
            css_func = f"{'rgb' if len(clr) == 3 else 'rgba'}"
            color_str = f"{', '.join(map(str, clr))}"
            return f"{css_func}({color_str})"
        return clr

    return await render_template(
        LYRIC_TEMPLATE,
        font_path=get_font_path_uri(),
        lrc=BBCODE_PARSER.format(txt),
        padding=padding,
        font_color=color_type_to_css(font_color),
        bg_color=color_type_to_css(bg_color),
        font_size=font_size,
        text_align=text_align,
    )
