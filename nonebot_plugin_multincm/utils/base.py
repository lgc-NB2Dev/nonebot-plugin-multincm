import json
import math
import time
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, TypeVar
from typing_extensions import ParamSpec

from yarl import URL

from ..config import config
from ..const import DEBUG_DIR, DEBUG_ROOT_DIR

if TYPE_CHECKING:
    from ..data_source import md

P = ParamSpec("P")
TR = TypeVar("TR")


def format_time(time: int) -> str:
    ss, _ = divmod(time, 1000)
    mm, ss = divmod(ss, 60)
    return f"{mm:0>2d}:{ss:0>2d}"


def format_alias(name: str, alias: Optional[List[str]] = None) -> str:
    return f'{name}（{"；".join(alias)}）' if alias else name


def format_artists(artists: List["md.Artist"]) -> str:
    return "、".join([x.name for x in artists])


def calc_page_number(index: int) -> int:
    return (index // config.ncm_list_limit) + 1


def calc_min_index(page: int) -> int:
    return (page - 1) * config.ncm_list_limit


def calc_min_max_index(page: int) -> Tuple[int, int]:
    min_index = calc_min_index(page)
    max_index = min_index + config.ncm_list_limit
    return min_index, max_index


def calc_max_page(total: int) -> int:
    return math.ceil(total / config.ncm_list_limit)


def is_debug_mode() -> bool:
    return DEBUG_ROOT_DIR.exists() and DEBUG_ROOT_DIR.is_dir()


def write_debug_file(filename: str, content: Any):
    filename = filename.format(time=round(time.time() * 1000))
    path = DEBUG_DIR / filename
    if isinstance(content, (bytes, bytearray)):
        path.write_bytes(content)
        return
    path.write_text(
        (
            content
            if isinstance(content, str)
            else json.dumps(content, ensure_ascii=False)
        ),
        "u8",
    )


def get_thumb_url(url: str, size: int) -> str:
    return str(URL(url).update_query(param=f"{size}y{size}"))


def build_item_link(item_type: str, item_id: int) -> str:
    return f"https://music.163.com/{item_type}?id={item_id}"
