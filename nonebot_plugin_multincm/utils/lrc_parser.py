import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Literal, Optional, TypeVar
from typing_extensions import TypeAlias

from ..config import config

if TYPE_CHECKING:
    from ..data_source import md

SK = TypeVar("SK", bound=str)


@dataclass
class LrcLine:
    time: int
    """Lyric Time (ms)"""
    lrc: str
    """Lyric Content"""
    skip_merge: bool = False


@dataclass
class LrcGroupLine(Generic[SK]):
    time: int
    """Lyric Time (ms)"""
    lrc: dict[SK, str]


LRC_TIME_REGEX = r"(?P<min>\d+):(?P<sec>\d+)([\.:](?P<mili>\d+))?(-(?P<meta>\d))?"
LRC_LINE_REGEX = re.compile(rf"^((\[{LRC_TIME_REGEX}\])+)(?P<lrc>.*)$", re.MULTILINE)


def parse_lrc(
    lrc: str,
    ignore_empty: bool = False,
    merge_empty: bool = True,
) -> list[LrcLine]:
    parsed = []
    for line in re.finditer(LRC_LINE_REGEX, lrc):
        lrc = line["lrc"].strip().replace("\u3000", " ")
        times = [x.groupdict() for x in re.finditer(LRC_TIME_REGEX, line[0])]

        parsed.extend(
            [
                LrcLine(
                    time=(
                        int(i["min"]) * 60 * 1000
                        + int(float(f"{i['sec']}.{i['mili'] or 0}") * 1000)
                    ),
                    lrc=lrc,
                    skip_merge=bool(i["meta"])
                    or lrc.startswith(("作词", "作曲", "编曲")),
                )
                for i in times
            ],
        )

    if ignore_empty:
        parsed = [x for x in parsed if x.lrc]

    elif merge_empty:
        new_parsed = []

        for line in parsed:
            if line.lrc or (new_parsed and new_parsed[-1].lrc and (not line.lrc)):
                new_parsed.append(line)

        if new_parsed and (not new_parsed[-1].lrc):
            new_parsed.pop()

        parsed = new_parsed

    parsed.sort(key=lambda x: x.time)
    return parsed


def strip_lrc_lines(lines: list[LrcLine]) -> list[LrcLine]:
    for lrc in lines:
        lrc.lrc = lrc.lrc.strip()
    return lines


def merge_lrc(
    lyric_groups: dict[SK, list[LrcLine]],
    main_group: Optional[SK] = None,
    threshold: int = 20,
    replace_empty_line: Optional[str] = None,
    skip_merge_group_name: Optional[SK] = None,
) -> list[LrcGroupLine[SK]]:
    lyric_groups = {k: v.copy() for k, v in lyric_groups.items()}
    for v in lyric_groups.values():
        while not v[-1].lrc:
            v.pop()

    if main_group is None:
        main_group, main_lyric = next(iter(lyric_groups.items()))
    else:
        main_lyric = lyric_groups[main_group]
    main_lyric = strip_lrc_lines(main_lyric)

    lyric_groups.pop(main_group)
    sub_lines = [(n, strip_lrc_lines(x)) for n, x in lyric_groups.items()]

    if replace_empty_line:
        for x in main_lyric:
            if not x.lrc:
                x.lrc = replace_empty_line
                x.skip_merge = True

    merged: list[LrcGroupLine] = []
    for main_line in main_lyric:
        if not main_line.lrc:
            continue

        main_time = main_line.time
        line_main_group = (
            skip_merge_group_name
            if main_line.skip_merge and skip_merge_group_name
            else main_group
        )
        line_group = LrcGroupLine(
            time=main_time,
            lrc={line_main_group: main_line.lrc},
        )

        for group, sub_lrc in sub_lines:
            for i, line in enumerate(sub_lrc):
                if (not line.lrc) or main_line.skip_merge:
                    continue

                if (main_time - threshold) <= line.time < (main_time + threshold):
                    for _ in range(i + 1):
                        it = sub_lrc.pop(0)  # noqa: B909
                        if it.lrc:
                            line_group.lrc[group] = it.lrc
                    break

        merged.append(line_group)

    rest_lrc_len = max(len(x[1]) for x in sub_lines)
    if rest_lrc_len:
        extra_lines = [
            LrcGroupLine(time=merged[-1].time + 1000, lrc={})
            for _ in range(rest_lrc_len)
        ]
        for group, line in sub_lines:
            for target, extra in zip(extra_lines, line):
                target.lrc[group] = extra.lrc

    return merged


NCMLrcGroupNameType: TypeAlias = Literal["main", "roma", "trans", "meta"]
NCM_MAIN_LRC_GROUP: NCMLrcGroupNameType = "main"

NCMLrcGroupLine: TypeAlias = LrcGroupLine[NCMLrcGroupNameType]


def normalize_lrc(lrc: "md.LyricData") -> Optional[list[NCMLrcGroupLine]]:
    def fmt_usr(usr: "md.User") -> str:
        return f"{usr.nickname} [{usr.user_id}]"

    raw = lrc.lrc
    if (not raw) or (not (raw_lrc := raw.lyric)):
        return None

    raw_lyric_groups: dict[NCMLrcGroupNameType, Optional[md.Lyric]] = {
        "main": raw,
        "roma": lrc.roma_lrc,
        "trans": lrc.trans_lrc,
    }
    lyrics: dict[NCMLrcGroupNameType, list[LrcLine]] = {
        k: x for k, v in raw_lyric_groups.items() if v and (x := parse_lrc(v.lyric))
    }
    empty_line = config.ncm_lrc_empty_line

    if not lyrics:
        lines = [
            LrcGroupLine(
                time=0,
                lrc={NCM_MAIN_LRC_GROUP: (x or empty_line or "")},
            )
            for x in raw_lrc.splitlines()
        ]

    else:
        if lyrics[NCM_MAIN_LRC_GROUP][-1].time >= 5940000:
            return None  # 纯音乐
        lines: list[NCMLrcGroupLine] = merge_lrc(
            lyrics,
            main_group=NCM_MAIN_LRC_GROUP,
            replace_empty_line=empty_line,
            skip_merge_group_name="meta",
        )

    if lrc.lyric_user or lrc.trans_user:
        if usr := lrc.lyric_user:
            lines.append(
                LrcGroupLine(
                    time=5940000,
                    lrc={"meta": f"歌词贡献者：{fmt_usr(usr)}"},
                ),
            )
        if usr := lrc.trans_user:
            lines.append(
                LrcGroupLine(
                    time=5940000,
                    lrc={"meta": f"翻译贡献者：{fmt_usr(usr)}"},
                ),
            )

    return lines
