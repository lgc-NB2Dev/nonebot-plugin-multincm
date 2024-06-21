import json
from functools import partial
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from nonebot.utils import run_sync
from pydantic import BaseModel
from pyncm.apis import WeapiCryptoRequest, cloudsearch as search
from pyncm.apis.cloudsearch import GetSearchResult
from pyncm.apis.playlist import GetPlaylistInfo
from pyncm.apis.track import GetTrackAudio, GetTrackDetail, GetTrackLyrics

from ...config import config
from ...utils import calc_min_index, is_debug_mode, write_debug_file
from .models import (
    LyricData,
    Playlist,
    PlaylistSearchResult,
    Privilege,
    Song,
    SongSearchResult,
    TrackAudio,
    VoiceBaseInfo,
    VoiceSearchResult,
)

TModel = TypeVar("TModel", bound=BaseModel)


async def ncm_request(api: Callable, *args, **kwargs) -> Dict[str, Any]:
    ret = await run_sync(api)(*args, **kwargs)
    if is_debug_mode():
        write_debug_file(f"{api.__name__}_{{time}}.json", json.dumps(ret))
    if ret.get("code", 200) != 200:
        raise RuntimeError(f"请求 {api.__name__} 失败\n{ret}")
    return ret


@overload
async def get_search_result(
    keyword: str,
    return_model: Type[TModel],
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
) -> Dict[str, Any]: ...


async def get_search_result(
    keyword: str,
    return_model: Optional[Type[TModel]] = None,
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> Union[Dict[str, Any], TModel]:
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


async def search_voice(keyword: str, page: int = 1) -> VoiceSearchResult:
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

    offset = calc_min_index(page)
    res = await ncm_request(SearchVoice)
    return VoiceSearchResult(**res["data"])


async def get_track_audio(
    song_ids: List[int],
    bit_rate: int = 999999,
    **kwargs,
) -> List[TrackAudio]:
    res = await ncm_request(GetTrackAudio, song_ids, bitrate=bit_rate, **kwargs)
    return [TrackAudio(**x) for x in cast(List[dict], res["data"])]


async def get_track_info(ids: List[int], **kwargs) -> List[Song]:
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


async def get_track_lrc(song_id: int) -> LyricData:
    res = await ncm_request(GetTrackLyrics, song_id)
    return LyricData(**res)


async def get_voice_info(program_id: int) -> VoiceBaseInfo:
    @WeapiCryptoRequest  # type: ignore
    def GetProgramDetail():  # noqa: N802
        return ("/api/dj/program/detail", {"id": program_id})

    res = await ncm_request(GetProgramDetail)
    return VoiceBaseInfo(**res["program"])


async def get_playlist_info(playlist_id: int) -> Any:
    res = await ncm_request(GetPlaylistInfo, playlist_id)
    return Playlist(**res["playlist"])
