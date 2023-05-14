from math import ceil
from typing import Dict

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.typing import T_State

from .config import config
from .data_source import get_track_audio, search_song
from .draw import draw_search_res
from .types import SongSearchResult
from .utils import format_alias, format_artists


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

    try:
        pic = draw_search_res(res, page)
    except:
        logger.exception("绘制歌曲列表失败")
        await matcher.finish("绘制歌曲列表失败，请检查后台输出")

    state["page"] = page
    cache[page] = res
    state["page_max"] = ceil(res.songCount / config.ncm_list_limit)
    return MessageSegment.image(pic)


cmd_matcher = on_command("点歌", aliases={"网易云", "wyy"})


@cmd_matcher.handle()
async def _(matcher: Matcher, arg_msg: Message = CommandArg()):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)


@cmd_matcher.got("arg", "请发送搜索内容")
async def _(matcher: Matcher, state: T_State, arg: str = ArgPlainText("arg")):
    param = arg.strip()
    if not param:
        await matcher.finish("消息无文本，放弃点歌")
    state["param"] = param
    state["page"] = 1
    state["cache"] = {}
    await matcher.pause(await get_page(matcher, state))


@cmd_matcher.handle()
async def _(matcher: Matcher, state: T_State, event: MessageEvent):
    arg = event.get_message().extract_plain_text().strip()
    page: int = state["page"]
    page_max: int = state["page_max"]
    cache: Dict[int, SongSearchResult] = state["cache"]

    if arg in ["退出", "0"]:
        await matcher.finish("已退出选择")

    if arg == "上一页":
        if page <= 1:
            await matcher.reject("已经是第一页了")
        await matcher.reject(await get_page(matcher, state, page - 1))

    if arg == "下一页":
        if page >= page_max:
            await matcher.reject("已经是最后一页了")
        await matcher.reject(await get_page(matcher, state, page + 1))

    if arg.isdigit():
        ori_index = int(arg) - 1
        page_index = ceil(ori_index / config.ncm_list_limit)
        index = ori_index % config.ncm_list_limit

        if (not (res := cache.get(page_index))) or (not (0 <= index < len(res.songs))):
            await matcher.reject("序号输入有误，请重新输入")

        song = res.songs[index]
        try:
            audio_info = await get_track_audio([song.id], song.privilege.pl)
        except:
            logger.exception("获取歌曲播放链接失败")
            await matcher.reject("获取歌曲播放链接失败，请检查后台输出")

        if not audio_info:
            await matcher.finish("抱歉，没有获取到歌曲播放链接")

        info = audio_info[0]
        await matcher.finish(
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

    await matcher.reject("非正确指令，请重新输入")
