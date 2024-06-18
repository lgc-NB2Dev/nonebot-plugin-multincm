import math
from typing import List, Optional, Tuple, TypeVar, cast
from typing_extensions import ParamSpec

from ..config import config
from ..data_source import md
from .lrc_parser import merge_lrc, parse_lrc

P = ParamSpec("P")
TR = TypeVar("TR")


def format_time(time: int) -> str:
    ss, _ = divmod(time, 1000)
    mm, ss = divmod(ss, 60)
    return f"{mm:0>2d}:{ss:0>2d}"


def format_alias(name: str, alias: List[str]) -> str:
    return f'{name}（{"；".join(alias)}）' if alias else name


def format_artists(artists: List[md.Artist]) -> str:
    return "、".join([x.name for x in artists])


def format_lrc(lrc: md.LyricData) -> Optional[str]:
    def fmt_usr(usr: md.User) -> str:
        return f"{usr.nickname} [{usr.user_id}]"

    raw = lrc.lrc
    if (not raw) or (not (raw_lrc := raw.lyric)):
        return None

    lyrics = [
        parse_lrc(x.lyric)
        for x in cast(List[Optional[md.Lyric]], [raw, lrc.roma_lrc, lrc.trans_lrc])
        if x
    ]
    lyrics = [x for x in lyrics if x]
    empty_line = config.ncm_lrc_empty_line

    lines = []
    if not lyrics:
        lines.extend(
            (
                "[i]该歌曲没有滚动歌词[/i]",
                "",
                empty_line,
                "",
                raw_lrc,
            ),
        )

    else:
        if lyrics[0][-1].time >= 5940000:
            return None  # 纯音乐

        only_one = len(lyrics) == 1
        for li in merge_lrc(*lyrics, replace_empty_line=empty_line):
            if not only_one:
                lines.append("")
            lines.append(f"[b]{li[0].lrc}[/b]")
            lines.extend([f"{x.lrc}" for x in li[1:]])

    if lrc.lyric_user or lrc.trans_user:
        lines.extend(("", empty_line, ""))
        if usr := lrc.lyric_user:
            lines.append(f"歌词贡献者：{fmt_usr(usr)}")
        if usr := lrc.trans_user:
            lines.append(f"翻译贡献者：{fmt_usr(usr)}")

    return "\n".join(lines).strip()


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
