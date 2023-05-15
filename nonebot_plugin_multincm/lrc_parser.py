import re
from dataclasses import dataclass
from enum import Enum
from typing import Callable, List, Optional, TypeVar

T = TypeVar("T")


@dataclass
class LrcLine:
    time: int
    """Lyric Time (ms)"""
    lrc: str
    """Lyric Content"""
    skip_merge: bool = False


class LyricMatchMode(Enum):
    EQUAL = 1
    CLOSEST = 2


LRC_TIME_REGEX = r"(?P<min>\d+):(?P<sec>\d+)([\.:](?P<mili>\d+))?(-(?P<meta>\d))?"
LRC_LINE_REGEX = re.compile(rf"^((\[{LRC_TIME_REGEX}\])+)(?P<lrc>.*)$", re.M)


def find_last(array: List[T], predicate: Callable[[T], bool]) -> Optional[T]:
    for i in range(len(array) - 1, -1, -1):
        it = array[i]
        if predicate(it):
            return it
    return None


def parse(lrc: str, ignore_empty: bool = False) -> List[LrcLine]:
    parsed = []
    for line in re.finditer(LRC_LINE_REGEX, lrc):
        lrc = line["lrc"].strip().replace("\u3000", " ")
        times = [x.groupdict() for x in re.finditer(LRC_TIME_REGEX, line[0])]

        parsed.extend(
            [
                LrcLine(
                    time=(
                        int(i["min"]) * 60 * 1000
                        + int(float(f'{i["sec"]}.{i["mili"]}') * 1000)
                    ),
                    lrc=lrc,
                    skip_merge=bool(i["meta"]) or lrc.startswith(("作词", "作曲", "编曲")),
                )
                for i in times
            ],
        )

    if ignore_empty:
        parsed = [x for x in parsed if x.lrc]

    parsed.sort(key=lambda x: x.time)
    return parsed


def merge(*lyrics: List[LrcLine], threshold: int = 20) -> List[List[LrcLine]]:
    lyrics = tuple(x.copy() for x in lyrics)

    for lrc in lyrics:
        while not lrc[-1].lrc:
            lrc.pop()

    main_lyric = lyrics[0]
    sub_lyrics = lyrics[1:]

    for x in main_lyric:
        if not x.lrc:
            x.lrc = "--------"

    merged: List[List[LrcLine]] = [[x] for x in main_lyric]
    for merged_line in merged:
        main_line = merged_line[0]
        main_time = main_line.time

        for sub_lrc in sub_lyrics:
            for i, line in enumerate(sub_lrc):
                if (not line.lrc) or main_line.skip_merge:
                    continue

                if (main_time - threshold) <= line.time < (main_time + threshold):
                    for _ in range(i + 1):
                        it = sub_lrc.pop(0)
                        if it.lrc:
                            merged_line.append(it)
                    break

    for sub_lrc in sub_lyrics:
        merged[-1].extend(sub_lrc)

    return merged
