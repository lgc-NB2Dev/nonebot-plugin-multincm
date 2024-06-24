from pathlib import Path
from typing import Literal, Optional, TypedDict

import jinja2
from cookit.jinja import make_register_jinja_filter_deco, register_all_filters
from nonebot_plugin_htmlrender import get_new_page

from ..config import config
from ..utils import is_debug_mode, write_debug_file

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)
register_all_filters(jinja_env)

register_filter = make_register_jinja_filter_deco(jinja_env)


class RenderConfig(TypedDict):
    font_family: Optional[str]
    plugin_version: str


def get_config() -> RenderConfig:
    from ..__init__ import __version__ as plugin_version

    return {
        "font_family": config.ncm_list_font_url,
        "plugin_version": plugin_version,
    }


async def render_template(name: str, **kwargs):
    return await jinja_env.get_template(name).render_async(
        config=get_config(),
        **kwargs,
    )


async def render_html(
    html: str,
    selector: str = "main",
    image_type: Literal["jpeg", "png"] = "jpeg",
) -> bytes:
    if is_debug_mode():
        write_debug_file("{time}.html", html)
    async with get_new_page() as page:
        await page.set_content(html)
        elem = await page.query_selector(selector)
        assert elem
        return await elem.screenshot(type=image_type)
