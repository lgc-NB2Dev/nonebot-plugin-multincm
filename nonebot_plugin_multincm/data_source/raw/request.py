from functools import partial
from typing import Any, Callable, Literal, Optional, TypeVar, Union, cast, overload
from typing_extensions import ParamSpec

from nonebot.utils import run_sync
from pydantic import BaseModel
from pyncm.apis import EapiCryptoRequest, WeapiCryptoRequest, cloudsearch as search
from pyncm.apis.album import GetAlbumInfo
from pyncm.apis.cloudsearch import GetSearchResult
from pyncm.apis.playlist import GetPlaylistInfo
from pyncm.apis.track import GetTrackAudio, GetTrackDetail, GetTrackLyrics

from ...config import config
from ...utils import calc_min_index, debug
from .models import (
    AlbumInfo,
    AlbumSearchResult,
    LyricData,
    Playlist,
    PlaylistSearchResult,
    Privilege,
    ProgramBaseInfo,
    ProgramSearchResult,
    Radio,
    RadioProgramList,
    RadioSearchResult,
    Song,
    SongSearchResult,
    TrackAudio,
)

TModel = TypeVar("TModel", bound=BaseModel)
P = ParamSpec("P")


class NCMResponseError(Exception):
    def __init__(self, name: str, data: dict[str, Any]):
        self.name = name
        self.data = data

    @property
    def code(self) -> Optional[int]:
        return self.data.get("code")

    @property
    def message(self) -> Optional[str]:
        return self.data.get("message")

    def __str__(self):
        return f"{self.name} failed: [{self.code}] {self.message}"


async def ncm_request(
    api: Callable[P, Any],
    *args: P.args,
    **kwargs: P.kwargs,
) -> dict[str, Any]:
    ret = await run_sync(api)(*args, **kwargs)
    debug.write(ret, f"{api.__name__}_{{time}}.json")
    if ret.get("code", 200) != 200:
        raise NCMResponseError(api.__name__, ret)
    return ret


@overload
async def get_search_result(
    keyword: str,
    return_model: type[TModel],
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> TModel: ...


@overload
async def get_search_result(
    keyword: str,
    return_model: Literal[None] = None,
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> dict[str, Any]: ...


async def get_search_result(
    keyword: str,
    return_model: Optional[type[TModel]] = None,
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> Union[dict[str, Any], TModel]:
    offset = calc_min_index(page)
    res = await ncm_request(
        GetSearchResult,
        keyword=keyword,
        limit=config.ncm_list_limit,
        offset=offset,
        stype=search_type,
        **kwargs,
    )
    result = res["result"]
    if return_model:
        return return_model(**result)
    return result


search_song = partial(
    get_search_result,
    search_type=search.SONG,
    return_model=SongSearchResult,
)
search_playlist = partial(
    get_search_result,
    search_type=search.PLAYLIST,
    return_model=PlaylistSearchResult,
)
search_album = partial(
    get_search_result,
    search_type=search.ALBUM,
    return_model=AlbumSearchResult,
)


async def search_radio(keyword: str, page: int = 1):
    offset = calc_min_index(page)

    @EapiCryptoRequest  # type: ignore
    def SearchRadio():  # noqa: N802
        return (
            "/eapi/search/voicelist/get",
            {
                "keyword": keyword,
                "scene": "normal",
                "limit": config.ncm_list_limit,
                "offset": offset or 0,
            },
        )

    res = await ncm_request(SearchRadio)
    return RadioSearchResult(**res["data"])


async def search_program(keyword: str, page: int = 1):
    offset = calc_min_index(page)

    @WeapiCryptoRequest  # type: ignore
    def SearchVoice():  # noqa: N802
        return (
            "/api/search/voice/get",
            {
                "keyword": keyword,
                "scene": "normal",
                "limit": config.ncm_list_limit,
                "offset": offset or 0,
            },
        )

    res = await ncm_request(SearchVoice)
    return ProgramSearchResult(**res["data"])


async def get_track_audio(
    song_ids: list[int],
    bit_rate: int = 999999,
    **kwargs,
) -> list[TrackAudio]:
    res = await ncm_request(GetTrackAudio, song_ids, bitrate=bit_rate, **kwargs)
    return [TrackAudio(**x) for x in cast("list[dict]", res["data"])]


async def get_track_info(ids: list[int], **kwargs) -> list[Song]:
    res = await ncm_request(GetTrackDetail, ids, **kwargs)
    privileges = {y.id: y for y in [Privilege(**x) for x in res["privileges"]]}
    return [
        Song(
            **x,
            privilege=(
                privileges[song_id]
                if (song_id := x["id"]) in privileges
                else Privilege(id=song_id, pl=128000)  # , plLevel="standard")
            ),
        )
        for x in res["songs"]
    ]


async def get_track_lrc(song_id: int):
    res = await ncm_request(GetTrackLyrics, str(song_id))
    return LyricData(**res)


async def get_radio_info(radio_id: int):
    @WeapiCryptoRequest  # type: ignore
    def GetRadioInfo():  # noqa: N802
        return ("/api/djradio/v2/get", {"id": radio_id})

    res = await ncm_request(GetRadioInfo)
    return Radio(**res["data"])


async def get_radio_programs(radio_id: int, page: int = 1):
    @WeapiCryptoRequest  # type: ignore
    def GetRadioPrograms():  # noqa: N802
        offset = calc_min_index(page)
        return (
            "/weapi/dj/program/byradio",
            {"radioId": radio_id, "limit": config.ncm_list_limit, "offset": offset},
        )

    res = await ncm_request(GetRadioPrograms)
    return RadioProgramList(**res)


async def get_program_info(program_id: int):
    @WeapiCryptoRequest  # type: ignore
    def GetProgramDetail():  # noqa: N802
        return ("/api/dj/program/detail", {"id": program_id})

    res = await ncm_request(GetProgramDetail)
    return ProgramBaseInfo(**res["program"])


async def get_playlist_info(playlist_id: int):
    res = await ncm_request(GetPlaylistInfo, playlist_id)
    return Playlist(**res["playlist"])


async def get_album_info(album_id: int):
    res = await ncm_request(GetAlbumInfo, str(album_id))
    return AlbumInfo(**res)
