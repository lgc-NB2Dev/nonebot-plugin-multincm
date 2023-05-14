from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.internal.matcher import Matcher
from nonebot.params import ArgPlainText, CommandArg

from .data_source import search_song
from .draw import draw_search_res

cmd_matcher = on_command("点歌", aliases={"网易云", "wyy"})


@cmd_matcher.handle()
async def _(matcher: Matcher, arg_msg: Message = CommandArg()):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("param", arg_msg)


@cmd_matcher.got("param", "请发送搜索内容")
async def _(matcher: Matcher, param: str = ArgPlainText("param")):
    if not param:
        await matcher.finish("消息无文本，放弃点歌")

    try:
        res = await search_song(param)
    except:
        logger.exception("搜索歌曲失败")
        await matcher.finish("搜索歌曲失败，请检查后台输出")

    if not res.songCount:
        await matcher.finish("没搜到任何歌曲捏")

    try:
        pic = draw_search_res(res)
    except:
        logger.exception("绘制歌曲列表失败")
        await matcher.finish("绘制歌曲列表失败，请检查后台输出")

    await matcher.pause(MessageSegment.image(pic))


@cmd_matcher.handle()
async def _(matcher: Matcher, event: MessageEvent):
    await matcher.finish(f"you sent {str(event)}\nwork in progress")
