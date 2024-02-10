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

import anyio
from nonebot import get_available_plugin_names, logger, require
from nonebot.utils import run_sync
from pydantic import BaseModel
from pyncm import (
    DumpSessionAsString,
    GetCurrentSession,
    LoadSessionFromString,
    SetCurrentSession,
)
from pyncm.apis import WeapiCryptoRequest, cloudsearch as search
from pyncm.apis.cloudsearch import GetSearchResult
from pyncm.apis.login import (
    GetCurrentLoginStatus,
    LoginViaAnonymousAccount,
    LoginViaCellphone,
    LoginViaEmail,
)
from pyncm.apis.playlist import GetPlaylistInfo
from pyncm.apis.track import GetTrackAudio, GetTrackDetail, GetTrackLyrics

from .config import config
from .const import DATA_PATH
from .types import (
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

SESSION_FILE = DATA_PATH / "session.cache"


def get_offset_by_page_num(page: int, limit: int = config.ncm_list_limit) -> int:
    return limit * (page - 1)


async def ncm_request(api: Callable, *args, **kwargs) -> Dict[str, Any]:
    ret = await run_sync(api)(*args, **kwargs)
    if ret.get("code", 200) != 200:
        raise RuntimeError(f"请求 {api.__name__} 失败\n{ret}")
    logger.debug(f"{api.__name__} - {ret}")
    return ret


@overload
async def get_search_result(
    keyword: str,
    return_model: Type[TModel],
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> TModel:
    ...


@overload
async def get_search_result(
    keyword: str,
    return_model: Literal[None] = None,
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> Dict[str, Any]:
    ...


async def get_search_result(
    keyword: str,
    return_model: Optional[Type[TModel]] = None,
    page: int = 1,
    search_type: int = search.SONG,
    **kwargs,
) -> Union[Dict[str, Any], TModel]:
    offset = get_offset_by_page_num(page)
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

    offset = get_offset_by_page_num(page)
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


async def login(retry: bool = True):
    if SESSION_FILE.exists():
        logger.info(f"使用缓存登录态 ({SESSION_FILE})")
        SetCurrentSession(
            LoadSessionFromString(
                (await anyio.Path(SESSION_FILE).read_text(encoding="u8")),
            ),
        )

    elif (config.ncm_phone or config.ncm_email) and (
        config.ncm_password or config.ncm_password_hash
    ):
        retry = False

        if config.ncm_phone:
            logger.info("使用手机号登录")
            await run_sync(LoginViaCellphone)(
                ctcode=config.ncm_ctcode,
                phone=config.ncm_phone,
                password=config.ncm_password or "",
                passwordHash=config.ncm_password_hash or "",
            )

        else:
            logger.info("使用邮箱登录")
            await run_sync(LoginViaEmail)(
                email=config.ncm_email or "",
                password=config.ncm_password or "",
                passwordHash=config.ncm_password_hash or "",
            )

        await anyio.Path(SESSION_FILE).write_text(
            DumpSessionAsString(GetCurrentSession()),
            encoding="u8",
        )

    else:
        retry = False
        logger.warning("账号或密码未填写，使用游客账号登录")
        await run_sync(LoginViaAnonymousAccount)()

    try:
        ret = cast(dict, await run_sync(GetCurrentLoginStatus)())
        assert ret["code"] == 200
        assert ret["account"]
    except Exception as e:
        if await (pth := anyio.Path(SESSION_FILE)).exists():
            await pth.unlink()

        if retry:
            logger.warning("恢复缓存会话失败，尝试使用正常流程登录")
            await login(retry=False)
            return

        raise RuntimeError("登录态异常，请重新登录") from e

    session = GetCurrentSession()
    logger.info(f"登录成功，欢迎您，{session.nickname} [{session.uid}]")


if "nonebot-plugin-ncm" in get_available_plugin_names():
    logger.info("nonebot-plugin-ncm 已安装，本插件将依赖其全局 Session")
    require("nonebot-plugin-ncm")

else:
    from nonebot import get_driver

    driver = get_driver()

    @driver.on_startup
    async def _():
        await login()
