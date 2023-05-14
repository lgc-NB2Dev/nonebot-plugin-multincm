from typing import List, Literal, Optional

from pydantic import BaseModel

BrLevel = Literal["hires", "lossless", "exhigh", "standard"]


class Artist(BaseModel):
    id: int  # noqa: A003
    name: str
    tns: List[str]
    alias: List[str]


class Album(BaseModel):
    id: int  # noqa: A003
    name: str
    picUrl: str  # noqa: N815
    tns: List[str]


class Privilege(BaseModel):
    pl: int
    plLevel: BrLevel  # noqa: N815


class Song(BaseModel):
    name: str
    id: int  # noqa: A003
    ar: List[Artist]
    alia: List[str]
    pop: float
    al: Album
    dt: int
    """歌曲时长，单位 ms"""
    privilege: Privilege


class QcReminder(BaseModel):
    qcReminderPart: str  # noqa: N815
    """纠正内容部分"""
    highLight: bool  # noqa: N815
    """部分是否高亮（可点击纠正）"""


class SearchQcReminder(BaseModel):
    qcReminders: List[QcReminder]  # noqa: N815
    qcReminderChannel: str  # noqa: N815


class SongSearchResult(BaseModel):
    searchQcReminder: Optional[SearchQcReminder]  # noqa: N815
    """搜索纠正"""
    songCount: int  # noqa: N815
    songs: List[Song]
