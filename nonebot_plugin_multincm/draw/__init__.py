from nonebot import require

from ..config import config
from .shared import SearchResp as SearchResp
from .shared import Table as Table
from .shared import TableHead as TableHead

if config.ncm_use_playwright:
    require("nonebot_plugin_htmlrender")

    from .playwright import draw_search_res as draw_search_res
    from .playwright import str_to_pic as str_to_pic

else:
    from .pil import draw_search_res as draw_search_res
    from .pil import str_to_pic as str_to_pic
