from dataclasses import dataclass
from math import ceil
from typing import List, NamedTuple, Optional

from pil_utils.types import HAlignType

from ..config import config


@dataclass()
class TableHead:
    name: str
    align: HAlignType = "left"
    min_width: Optional[int] = None
    max_width: Optional[int] = None


class Table(NamedTuple):
    head: List[TableHead]
    rows: List[List[str]]


@dataclass()
class TablePage:
    table: Table
    calling: str
    current_page: int
    max_count: int

    @property
    def max_page(self) -> int:
        return ceil(self.max_count / config.ncm_list_limit)
