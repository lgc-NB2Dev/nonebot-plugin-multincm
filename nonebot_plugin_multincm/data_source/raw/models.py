from typing import Literal, Optional
from typing_extensions import TypeAlias

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
    tns: Optional[list[str]] = None
    alias: Optional[list[str]] = None


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
    tns: Optional[list[str]] = None
    privilege: Optional[Privilege] = None


class QcReminder(CamelAliasModel):
    qc_reminder_part: str
    """纠正内容部分"""
    high_light: bool
    """部分是否高亮（可点击纠正）"""


class SearchQcReminder(CamelAliasModel):
    qc_reminders: list[QcReminder]
    qc_reminder_channel: str


class SongSearchResult(CamelAliasModel):
    search_qc_reminder: Optional[SearchQcReminder] = None
    """搜索纠正"""
    song_count: int
    songs: Optional[list[Song]] = None


class TrackAudio(CamelAliasModel):
    id: int
    url: str
    br: int
    size: int
    md5: str
    level: Optional[str] = None
    encode_type: Optional[str] = None
    time: int


class User(CamelAliasModel):
    id: int
    user_id: int = Field(..., alias="userid")
    nickname: str


class Lyric(CamelAliasModel):
    version: int
    lyric: str


class LyricData(CamelAliasModel):
    trans_user: Optional[User] = None
    lyric_user: Optional[User] = None
    lrc: Optional[Lyric] = None
    trans_lrc: Optional[Lyric] = Field(None, alias="tlyric")
    roma_lrc: Optional[Lyric] = Field(None, alias="romalrc")


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
    second_category_id: Optional[int] = None
    category: str
    second_category: Optional[str] = None
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
    resources: Optional[list[ProgramResource]] = None
    total_count: int
    search_qc_reminder: Optional[SearchQcReminder] = None


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
    description: Optional[str] = None


class Playlist(BasePlaylist):
    # tracks: List[Song]
    track_ids: list[TrackId]
    book_count: int = Field(alias="subscribedCount")
    share_count: int
    comment_count: int


class PlaylistSearchResult(CamelAliasModel):
    playlists: Optional[list[BasePlaylist]] = None
    playlist_count: int
    search_qc_reminder: Optional[SearchQcReminder] = None


class RadioResource(CamelAliasModel):
    base_info: RadioBaseInfo


class RadioSearchResult(CamelAliasModel):
    resources: Optional[list[RadioResource]] = None
    total_count: int
    search_qc_reminder: Optional[SearchQcReminder] = None


class RadioProgramList(CamelAliasModel):
    count: int
    programs: list[ProgramBaseInfo]


class AlbumSearchResult(CamelAliasModel):
    albums: Optional[list[Album]] = None
    album_count: int


class AlbumInfo(CamelAliasModel):
    album: Album
    songs: list[Song]
