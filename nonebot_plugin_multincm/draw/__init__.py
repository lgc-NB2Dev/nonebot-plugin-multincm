from nonebot import require

from ..config import config
from .shared import Table as Table
from .shared import TableHead as TableHead
from .shared import TablePage as TablePage

if config.ncm_use_playwright:
    require("nonebot_plugin_htmlrender")

    from .playwright import draw_table_page as draw_table_page
    from .playwright import str_to_pic as str_to_pic

else:
    from .pil import draw_table_page as draw_table_page
    from .pil import str_to_pic as str_to_pic
