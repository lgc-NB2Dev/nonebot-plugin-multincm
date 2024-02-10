from typing import List, Optional, TypeVar, cast
from typing_extensions import ParamSpec

from . import lrc_parser
from .config import config
from .types import Artist, Lyric, LyricData, User

P = ParamSpec("P")
TR = TypeVar("TR")


def format_time(time: int) -> str:
    s, _ = divmod(time, 1000)
    m, s = divmod(s, 60)
    return f"{m:0>2d}:{s:0>2d}"


def format_alias(name: str, alias: List[str]) -> str:
    return f'{name}（{"；".join(alias)}）' if alias else name


def format_artists(artists: List[Artist]) -> str:
    return "、".join([x.name for x in artists])


def format_lrc(lrc: LyricData) -> Optional[str]:
    def fmt_usr(usr: User) -> str:
        return f"{usr.nickname} [{usr.userid}]"

    raw = lrc.lrc
    if (not raw) or (not (raw_lrc := raw.lyric)):
        return None

    lyrics = [
        lrc_parser.parse(x.lyric)
        for x in cast(List[Optional[Lyric]], [raw, lrc.romalrc, lrc.tlyric])
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
        for li in lrc_parser.merge(*lyrics, replace_empty_line=empty_line):
            if not only_one:
                lines.append("")
            lines.append(f"[b]{li[0].lrc}[/b]")
            lines.extend([f"{x.lrc}" for x in li[1:]])

    if lrc.lyricUser or lrc.transUser:
        lines.extend(("", empty_line, ""))
        if usr := lrc.lyricUser:
            lines.append(f"歌词贡献者：{fmt_usr(usr)}")
        if usr := lrc.transUser:
            lines.append(f"翻译贡献者：{fmt_usr(usr)}")

    return "\n".join(lines).strip()
