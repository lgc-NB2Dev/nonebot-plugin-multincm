# ruff: noqa: A003 N815

from typing import List, Literal, Optional, Union
from typing_extensions import TypeAlias

from pydantic import BaseModel, Field

BrLevelType = Literal["hires", "lossless", "exhigh", "higher", "standard", "none"]

SearchRespModelType = Union[
    "SongSearchResult",
    "VoiceSearchResult",
    "PlaylistSearchResult",
]
PlaylistRespModelType: TypeAlias = "Playlist"
SongInfoModelType = Union["Song", "VoiceBaseInfo"]


class Artist(BaseModel):
    id: int
    name: str
    tns: List[str]
    alias: List[str]


class Album(BaseModel):
    id: int
    name: str
    picUrl: str
    tns: List[str]


class Privilege(BaseModel):
    id: int
    pl: int
    # plLevel: BrLevel


class Song(BaseModel):
    name: str
    id: int
    ar: List[Artist]
    alia: List[str]
    pop: float
    al: Album
    dt: int
    """歌曲时长，单位 ms"""
    privilege: Optional[Privilege]


class QcReminder(BaseModel):
    qcReminderPart: str
    """纠正内容部分"""
    highLight: bool
    """部分是否高亮（可点击纠正）"""


class SearchQcReminder(BaseModel):
    qcReminders: List[QcReminder]
    qcReminderChannel: str


class SongSearchResult(BaseModel):
    searchQcReminder: Optional[SearchQcReminder]
    """搜索纠正"""
    songCount: int
    songs: Optional[List[Song]]


class TrackAudio(BaseModel):
    id: int
    url: str
    br: int
    size: int
    md5: str
    level: Optional[str]
    encodeType: Optional[str]
    time: int


class User(BaseModel):
    id: int
    userid: int
    nickname: str


class Lyric(BaseModel):
    version: int
    lyric: str


class LyricData(BaseModel):
    transUser: Optional[User]
    lyricUser: Optional[User]
    lrc: Optional[Lyric]
    tlyric: Optional[Lyric]
    romalrc: Optional[Lyric]


class DJ(BaseModel):
    userId: int
    nickname: str
    avatarUrl: str
    gender: int
    signature: str
    backgroundUrl: str


class Radio(BaseModel):
    id: int
    name: str
    picUrl: str
    desc: str
    subCount: int
    programCount: int
    categoryId: int
    secondCategoryId: Optional[int]
    category: str
    secondCategory: Optional[str]
    lastProgramId: int


class VoiceBaseInfo(BaseModel):
    id: int
    mainTrackId: int
    name: str
    coverUrl: str
    description: str
    dj: DJ
    radio: Radio
    duration: int
    listenerCount: int
    shareCount: int
    likedCount: int
    commentCount: int
    commentThreadId: str


class VoiceResource(BaseModel):
    baseInfo: VoiceBaseInfo


class VoiceSearchResult(BaseModel):
    resources: Optional[List[VoiceResource]]
    totalCount: int
    searchQcReminder: Optional[SearchQcReminder]


class TrackId(BaseModel):
    id: int


class PlaylistCreator(BaseModel):
    userId: int
    nickname: str


class PlaylistFromSearch(BaseModel):
    id: int
    name: str
    coverImgUrl: str
    creator: PlaylistCreator
    trackCount: int
    playCount: int
    bookCount: int
    description: Optional[str]


class Playlist(PlaylistFromSearch):
    bookCount: int = Field(alias="subscribedCount")
    tracks: List[Song]
    trackIds: List[TrackId]


class PlaylistSearchResult(BaseModel):
    playlists: Optional[List[PlaylistFromSearch]]
    playlistCount: int
    searchQcReminder: Optional[SearchQcReminder]
