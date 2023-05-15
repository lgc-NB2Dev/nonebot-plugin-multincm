import re
from contextlib import suppress
from math import ceil
from typing import Any, Dict, Optional

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.typing import T_State

from .config import config
from .data_source import get_track_audio, get_track_info, get_track_lrc, search_song
from .draw import draw_search_res, format_lrc, str_to_pic
from .types import Song, SongSearchResult
from .utils import format_alias, format_artists

SONG_ID_REGEX = re.compile(r"music\.163\.com(.*)(song|url)/?\?id=(?P<id>[0-9]+)(|&)")

song_msg_id_cache: Dict[int, int] = {}


def extract_id_from_text(text: str) -> Optional[int]:
    res = re.search(SONG_ID_REGEX, text)
    return int(res["id"]) if res else None


async def cache_music_msg_rule(event: MessageEvent, state: T_State) -> bool:
    if reply := event.reply:
        song_id = song_msg_id_cache.get(reply.message_id)
        if song_id:
            state["song_id"] = song_id
            return True

    return False


async def reply_music_rule(event: MessageEvent, state: T_State) -> bool:
    if await cache_music_msg_rule(event, state):
        return True

    if reply := event.reply:
        song_id = extract_id_from_text(str(reply.message))
        if song_id:
            state["song_id"] = song_id
            return True

    return False


async def send_music(matcher: Matcher, song: Song):
    try:
        audio_info = await get_track_audio(
            [song.id],
            999999 if song.privilege.plLevel == "none" else song.privilege.pl,
        )
    except:
        logger.exception("获取歌曲播放链接失败")
        await matcher.finish("获取歌曲播放链接失败，请检查后台输出")

    if not audio_info:
        await matcher.finish("抱歉，没有获取到歌曲播放链接")

    info = audio_info[0]
    ret: Dict[str, Any] = await matcher.send(
        MessageSegment(
            "music",
            {
                "type": "custom",
                "subtype": "163",
                "url": info.url,
                "voice": info.url,
                "title": format_alias(song.name, song.alia),
                "content": format_artists(song.ar),
                "image": song.al.picUrl,
            },
        ),
    )
    print(ret)
    if msg_id := ret.get("message_id"):
        song_msg_id_cache[msg_id] = song.id
    await matcher.finish()


async def get_cache_by_index(
    cache: Dict[int, SongSearchResult],
    arg: int,
) -> Optional[Song]:
    ori_index = arg - 1
    page_index = ceil(ori_index / config.ncm_list_limit)
    page_index = 1 if page_index == 0 else page_index
    index = ori_index % config.ncm_list_limit

    if (not (res := cache.get(page_index))) or (not (0 <= index < len(res.songs))):
        return None

    return res.songs[index]


async def get_page(
    matcher: Matcher,
    state: T_State,
    page: int = 1,
) -> MessageSegment:
    param: str = state["param"]
    cache: Dict[int, SongSearchResult] = state["cache"]

    if not (res := cache.get(page)):
        try:
            res = await search_song(param, page=page)
        except:
            logger.exception("搜索歌曲失败")
            await matcher.finish("搜索歌曲失败，请检查后台输出")

        if not res.songCount:
            await matcher.finish("没搜到任何歌曲捏")

    state["page"] = page
    cache[page] = res
    state["page_max"] = ceil(res.songCount / config.ncm_list_limit)

    if page == 1 and len(res.songs) == 1:
        await get_cache_by_index(cache, 1)

    try:
        pic = draw_search_res(res, page)
    except:
        logger.exception("绘制歌曲列表失败")
        await matcher.finish("绘制歌曲列表失败，请检查后台输出")

    return MessageSegment.image(pic)


cmd_pick_song = on_command("点歌", aliases={"网易云", "wyy"})


@cmd_pick_song.handle()
async def _(matcher: Matcher, arg_msg: Message = CommandArg()):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)


@cmd_pick_song.got("arg", "请发送搜索内容")
async def _(matcher: Matcher, state: T_State, arg: str = ArgPlainText("arg")):
    param = arg.strip()
    if not param:
        await matcher.finish("消息无文本，放弃点歌")

    if param.isdigit():
        song = []
        with suppress(Exception):
            song = await get_track_info([int(param)])
        if song:
            await matcher.send("检测到输入了音乐 ID，将直接获取并发送对应歌曲")
            await send_music(matcher, song[0])

    state["param"] = param
    state["page"] = 1
    state["cache"] = {}
    await matcher.pause(await get_page(matcher, state))


@cmd_pick_song.handle()
async def _(matcher: Matcher, state: T_State, event: MessageEvent):
    arg = event.get_message().extract_plain_text().strip()
    page: int = state["page"]
    page_max: int = state["page_max"]

    if arg in ["退出", "tc", "exit", "e", "0"]:
        await matcher.finish("已退出选择")

    if arg in ["上一页", "syy", "previous", "p"]:
        if page <= 1:
            await matcher.reject("已经是第一页了")
        await matcher.reject(await get_page(matcher, state, page - 1))

    if arg in ["下一页", "xyy", "next", "n"]:
        if page >= page_max:
            await matcher.reject("已经是最后一页了")
        await matcher.reject(await get_page(matcher, state, page + 1))

    if arg.isdigit():
        cache = state["cache"]
        song = await get_cache_by_index(cache, int(arg))
        if not song:
            await matcher.reject("序号输入有误，请重新输入")
        await send_music(matcher, song)

    await matcher.reject("非正确指令，请重新输入")


cmd_get_song = on_command(
    "解析",
    aliases={"resolve", "parse", "get"},
    rule=reply_music_rule,
)


@cmd_get_song.handle()
async def _(matcher: Matcher, state: T_State):
    song_id: int = state["song_id"]

    try:
        song = await get_track_info([song_id])
    except:
        logger.exception("获取歌曲信息失败")
        await matcher.finish("获取歌曲信息失败，请检查后台输出")

    if not song:
        await matcher.finish("未获取到对应歌曲信息")

    await send_music(matcher, song[0])


cmd_get_lrc = on_command(
    "歌词",
    aliases={"lrc", "lyric", "lyrics"},
    rule=reply_music_rule,
)


@cmd_get_lrc.handle()
async def _(matcher: Matcher, state: T_State):
    song_id: int = state["song_id"]

    try:
        lrc_data = await get_track_lrc(song_id)
    except:
        logger.exception("获取歌曲歌词失败")
        await matcher.finish("获取歌曲歌词失败，请检查后台输出")

    lrc = format_lrc(lrc_data)
    if not lrc:
        await matcher.finish("该歌曲没有歌词")

    await matcher.finish(MessageSegment.image(str_to_pic(lrc)))


cmd_get_cache_link = on_command("链接", aliases={"link"}, rule=reply_music_rule)


@cmd_get_cache_link.handle()
async def _(matcher: Matcher, state: T_State):
    song_id: int = state["song_id"]
    await matcher.finish(f"https://music.163.com/song?id={song_id}")
