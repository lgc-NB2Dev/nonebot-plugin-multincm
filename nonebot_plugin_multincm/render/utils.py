from pathlib import Path
from typing import Literal, Optional, TypedDict

import jinja2
from cookit.jinja import register_all_filters
from nonebot_plugin_htmlrender import get_new_page

from ..config import config
from ..utils import DEV_HTML_PATH, is_dev_mode

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)
register_all_filters(jinja_env)


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
    if is_dev_mode():
        DEV_HTML_PATH.write_text(html, "u8")
    async with get_new_page() as page:
        await page.set_content(html)
        elem = await page.query_selector(selector)
        assert elem
        return await elem.screenshot(type=image_type)
