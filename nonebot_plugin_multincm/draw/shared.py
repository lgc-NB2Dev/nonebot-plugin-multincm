from dataclasses import dataclass
from typing import List, Optional, Tuple

from pil_utils.types import HAlignType

from ..config import config
from ..types import SongSearchResult, VoiceSearchResult
from ..utils import format_alias, format_artists, format_time


@dataclass()
class TableHead:
    name: str
    align: HAlignType = "left"
    min_width: Optional[int] = None
    max_width: Optional[int] = None


def get_song_search_res_table(
    res: SongSearchResult,
    index_offset: int = 0,
) -> Tuple[List[TableHead], List[List[str]]]:
    return (
        [
            TableHead("序号", align="right"),
            TableHead("歌名", max_width=config.ncm_max_name_len),
            TableHead("歌手", max_width=config.ncm_max_artist_len),
            TableHead("时长", align="center"),
            TableHead("热度", align="center"),
        ],
        [
            [
                f"[b]{i + index_offset + 1}[/b]",
                format_alias(x.name, x.alia),
                format_artists(x.ar),
                format_time(x.dt),
                f"{int(x.pop)}",
            ]
            for i, x in enumerate(res.songs)
        ],
    )


def get_voice_search_res_table(
    res: VoiceSearchResult,
    index_offset: int = 0,
) -> Tuple[List[TableHead], List[List[str]]]:
    if not res.resources:
        raise ValueError

    return (
        [
            TableHead("序号", align="right"),
            TableHead("节目", max_width=config.ncm_max_name_len),
            TableHead("电台", max_width=config.ncm_max_name_len),
            TableHead("台主", max_width=config.ncm_max_artist_len),
            TableHead("时长", align="center"),
        ],
        [
            [
                f"[b]{i + index_offset + 1}[/b]",
                x.baseInfo.name,
                x.baseInfo.radio.name,
                x.baseInfo.dj.nickname,
                format_time(x.baseInfo.duration),
            ]
            for i, x in enumerate(res.resources)
        ],
    )
