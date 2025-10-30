from typing import Literal, TypeAlias

from cookit import camel_case
from cookit.pyd import model_with_alias_generator
from pydantic import BaseModel, Field

BrLevelType: TypeAlias = Literal[
    "hires",
    "lossless",
    "exhigh",
    "higher",
    "standard",
    "none",
]


@model_with_alias_generator(camel_case)
class Artist(BaseModel):
    id: int
    name: str
    tns: list[str] | None = None
    alias: list[str] | None = None


@model_with_alias_generator(camel_case)
class BaseAlbum(BaseModel):
    id: int
    name: str
    pic_url: str


class Album(BaseAlbum):
    size: int
    artists: list[Artist]


@model_with_alias_generator(camel_case)
class Privilege(BaseModel):
    id: int
    pl: int
    # plLevel: BrLevel


@model_with_alias_generator(camel_case)
class Song(BaseModel):
    name: str
    id: int
    ar: list[Artist]
    alias: list[str] = Field(..., alias="alia")
    pop: int
    al: BaseAlbum
    dt: int
    """歌曲时长，单位 ms"""
    tns: list[str] | None = None
    privilege: Privilege | None = None


@model_with_alias_generator(camel_case)
class QcReminder(BaseModel):
    qc_reminder_part: str
    """纠正内容部分"""
    high_light: bool
    """部分是否高亮（可点击纠正）"""


@model_with_alias_generator(camel_case)
class SearchQcReminder(BaseModel):
    qc_reminders: list[QcReminder]
    qc_reminder_channel: str


@model_with_alias_generator(camel_case)
class SongSearchResult(BaseModel):
    search_qc_reminder: SearchQcReminder | None = None
    """搜索纠正"""
    song_count: int
    songs: list[Song] | None = None


@model_with_alias_generator(camel_case)
class TrackAudio(BaseModel):
    id: int
    url: str
    br: int
    size: int
    md5: str
    level: str | None = None
    encode_type: str | None = None
    time: int


@model_with_alias_generator(camel_case)
class User(BaseModel):
    id: int
    user_id: int = Field(..., alias="userid")
    nickname: str


@model_with_alias_generator(camel_case)
class Lyric(BaseModel):
    version: int
    lyric: str


@model_with_alias_generator(camel_case)
class LyricData(BaseModel):
    trans_user: User | None = None
    lyric_user: User | None = None
    lrc: Lyric | None = None
    trans_lrc: Lyric | None = Field(None, alias="tlyric")
    roma_lrc: Lyric | None = Field(None, alias="romalrc")


@model_with_alias_generator(camel_case)
class DJ(BaseModel):
    user_id: int
    nickname: str
    avatar_url: str
    gender: int
    signature: str
    background_url: str


@model_with_alias_generator(camel_case)
class BaseRadio(BaseModel):
    id: int
    name: str
    pic_url: str
    desc: str
    sub_count: int
    program_count: int
    play_count: int
    category_id: int
    second_category_id: int | None = None
    category: str
    second_category: str | None = None
    last_program_id: int


class RadioBaseInfo(BaseRadio):
    dj: DJ


class Radio(RadioBaseInfo):
    share_count: int
    liked_count: int
    comment_count: int


@model_with_alias_generator(camel_case)
class ProgramBaseInfo(BaseModel):
    id: int
    main_track_id: int
    name: str
    cover_url: str
    description: str
    dj: DJ
    radio: BaseRadio
    duration: int
    listener_count: int
    share_count: int
    liked_count: int
    comment_count: int
    comment_thread_id: str


@model_with_alias_generator(camel_case)
class ProgramResource(BaseModel):
    base_info: ProgramBaseInfo


@model_with_alias_generator(camel_case)
class ProgramSearchResult(BaseModel):
    resources: list[ProgramResource] | None = None
    total_count: int
    search_qc_reminder: SearchQcReminder | None = None


@model_with_alias_generator(camel_case)
class TrackId(BaseModel):
    id: int


@model_with_alias_generator(camel_case)
class PlaylistCreator(BaseModel):
    user_id: int
    nickname: str


@model_with_alias_generator(camel_case)
class BasePlaylist(BaseModel):
    id: int
    name: str
    cover_img_url: str
    creator: PlaylistCreator
    track_count: int
    play_count: int
    book_count: int
    description: str | None = None


class Playlist(BasePlaylist):
    # tracks: List[Song]
    track_ids: list[TrackId]
    book_count: int = Field(alias="subscribedCount")
    share_count: int
    comment_count: int


@model_with_alias_generator(camel_case)
class PlaylistSearchResult(BaseModel):
    playlists: list[BasePlaylist] | None = None
    playlist_count: int
    search_qc_reminder: SearchQcReminder | None = None


@model_with_alias_generator(camel_case)
class RadioResource(BaseModel):
    base_info: RadioBaseInfo


@model_with_alias_generator(camel_case)
class RadioSearchResult(BaseModel):
    resources: list[RadioResource] | None = None
    total_count: int
    search_qc_reminder: SearchQcReminder | None = None


@model_with_alias_generator(camel_case)
class RadioProgramList(BaseModel):
    count: int
    programs: list[ProgramBaseInfo]


@model_with_alias_generator(camel_case)
class AlbumSearchResult(BaseModel):
    albums: list[Album] | None = None
    album_count: int


@model_with_alias_generator(camel_case)
class AlbumInfo(BaseModel):
    album: Album
    songs: list[Song]
