from pathlib import Path
from typing import Literal

import jinja2
from nonebot_plugin_htmlrender import get_new_page

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
    enable_async=True,
)


async def render_html(
    html: str,
    selector: str = "main",
    image_type: Literal["jpeg", "png"] = "jpeg",
) -> bytes:
    async with get_new_page() as page:
        await page.set_content(html)
        elem = await page.query_selector(selector)
        assert elem
        return await elem.screenshot(type=image_type)
