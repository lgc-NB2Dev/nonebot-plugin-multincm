from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.typing import T_State

from .data_source import get_track_audio, search_song
from .draw import draw_search_res
from .types import SongSearchResult
from .utils import format_alias, format_artists

cmd_matcher = on_command("点歌", aliases={"网易云", "wyy"})


@cmd_matcher.handle()
async def _(matcher: Matcher, arg_msg: Message = CommandArg()):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("param", arg_msg)


@cmd_matcher.got("param", "请发送搜索内容")
async def _(matcher: Matcher, state: T_State, param: str = ArgPlainText("param")):
    param = param.strip()
    if not param:
        await matcher.finish("消息无文本，放弃点歌")

    try:
        res = await search_song(param)
    except:
        logger.exception("搜索歌曲失败")
        await matcher.finish("搜索歌曲失败，请检查后台输出")

    if not res.songCount:
        await matcher.finish("没搜到任何歌曲捏")

    state["res"] = res

    try:
        pic = draw_search_res(res)
    except:
        logger.exception("绘制歌曲列表失败")
        await matcher.finish("绘制歌曲列表失败，请检查后台输出")

    await matcher.pause(MessageSegment.image(pic))


@cmd_matcher.handle()
async def _(matcher: Matcher, state: T_State, event: MessageEvent):
    arg = event.get_message().extract_plain_text().strip()
    res: SongSearchResult = state["res"]

    if arg in ["退出", "0"]:
        await matcher.finish("已退出选择")

    if arg == "上一页":
        await matcher.finish("开发中awa")

    if arg == "下一页":
        await matcher.finish("开发中qwq")

    if arg.isdigit():
        index = int(arg)
        if not 0 < index <= len(res.songs):
            await matcher.reject("序号输入有误，请重新输入")

        song = res.songs[index - 1]
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
                    "audio": info.url,
                    "title": format_alias(song.name, song.alia),
                    "content": format_artists(song.ar),
                    "image": song.al.picUrl,
                },
            ),
        )

    await matcher.reject("非正确指令，请重新输入")
