from nonebot import require

from ..config import config
from .shared import Table as Table, TableHead as TableHead, TablePage as TablePage

if config.ncm_use_playwright:
    require("nonebot_plugin_htmlrender")

    from .playwright import draw_table_page as draw_table_page, str_to_pic as str_to_pic

else:
    from .pil import draw_table_page as draw_table_page, str_to_pic as str_to_pic
