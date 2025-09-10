from typing import Literal, TypeAlias

from cookit.pyd import CamelAliasModel
from pydantic import Field

BrLevelType: TypeAlias = Literal[
    "hires",
    "lossless",
    "exhigh",
    "higher",
    "standard",
    "none",
]


class Artist(CamelAliasModel):
    id: int
    name: str
    tns: list[str] | None = None
    alias: list[str] | None = None


class BaseAlbum(CamelAliasModel):
    id: int
    name: str
    pic_url: str


class Album(BaseAlbum):
    size: int
    artists: list[Artist]


class Privilege(CamelAliasModel):
    id: int
    pl: int
    # plLevel: BrLevel


class Song(CamelAliasModel):
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


class QcReminder(CamelAliasModel):
    qc_reminder_part: str
    """纠正内容部分"""
    high_light: bool
    """部分是否高亮（可点击纠正）"""


class SearchQcReminder(CamelAliasModel):
    qc_reminders: list[QcReminder]
    qc_reminder_channel: str


class SongSearchResult(CamelAliasModel):
    search_qc_reminder: SearchQcReminder | None = None
    """搜索纠正"""
    song_count: int
    songs: list[Song] | None = None


class TrackAudio(CamelAliasModel):
    id: int
    url: str
    br: int
    size: int
    md5: str
    level: str | None = None
    encode_type: str | None = None
    time: int


class User(CamelAliasModel):
    id: int
    user_id: int = Field(..., alias="userid")
    nickname: str


class Lyric(CamelAliasModel):
    version: int
    lyric: str


class LyricData(CamelAliasModel):
    trans_user: User | None = None
    lyric_user: User | None = None
    lrc: Lyric | None = None
    trans_lrc: Lyric | None = Field(None, alias="tlyric")
    roma_lrc: Lyric | None = Field(None, alias="romalrc")


class DJ(CamelAliasModel):
    user_id: int
    nickname: str
    avatar_url: str
    gender: int
    signature: str
    background_url: str


class BaseRadio(CamelAliasModel):
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


class ProgramBaseInfo(CamelAliasModel):
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


class ProgramResource(CamelAliasModel):
    base_info: ProgramBaseInfo


class ProgramSearchResult(CamelAliasModel):
    resources: list[ProgramResource] | None = None
    total_count: int
    search_qc_reminder: SearchQcReminder | None = None


class TrackId(CamelAliasModel):
    id: int


class PlaylistCreator(CamelAliasModel):
    user_id: int
    nickname: str


class BasePlaylist(CamelAliasModel):
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


class PlaylistSearchResult(CamelAliasModel):
    playlists: list[BasePlaylist] | None = None
    playlist_count: int
    search_qc_reminder: SearchQcReminder | None = None


class RadioResource(CamelAliasModel):
    base_info: RadioBaseInfo


class RadioSearchResult(CamelAliasModel):
    resources: list[RadioResource] | None = None
    total_count: int
    search_qc_reminder: SearchQcReminder | None = None


class RadioProgramList(CamelAliasModel):
    count: int
    programs: list[ProgramBaseInfo]


class AlbumSearchResult(CamelAliasModel):
    albums: list[Album] | None = None
    album_count: int


class AlbumInfo(CamelAliasModel):
    album: Album
    songs: list[Song]
