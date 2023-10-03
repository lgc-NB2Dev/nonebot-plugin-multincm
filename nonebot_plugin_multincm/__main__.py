import asyncio
import random
from typing import List, NoReturn, Optional, Type, Union, cast

from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment
from nonebot.matcher import Matcher, current_bot, current_matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.typing import T_State

from .config import config
from .draw import SearchResp, draw_search_res
from .providers import BaseSearcher, BaseSong, searchers

KEY_SEARCHER_TYPE = "searcher_type"
KEY_SEARCHER = "searcher"
KEY_LIST_MSG_ID = "list_msg_id"

EXIT_COMMAND = ("退出", "tc", "取消", "qx", "quit", "q", "exit", "e", "cancel", "c", "0")
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")

# region util funcs


async def delete_list_msg(msg_id: List[int], bot: Bot):
    for i in msg_id:
        await asyncio.sleep(random.uniform(*config.ncm_delete_list_msg_delay))
        try:
            await bot.delete_msg(message_id=i)
        except Exception as e:
            logger.warning(f"撤回消息 {msg_id} 失败: {e!r}")


async def finish_with_delete_msg(
    msg: Optional[Union[str, MessageSegment, Message]] = None,
) -> NoReturn:
    matcher = current_matcher.get()
    msg_id = current_matcher.get().state.get(KEY_LIST_MSG_ID)

    if not config.ncm_delete_list_msg:
        await matcher.finish()

    if msg_id:
        bot = cast(Bot, current_bot.get())
        asyncio.create_task(delete_list_msg(msg_id, bot))

    await matcher.finish(msg)


async def send_search_resp(resp: SearchResp, reject: bool = False, pause: bool = False):
    matcher = current_matcher.get()
    state = matcher.state

    try:
        pic = await draw_search_res(resp)
    except Exception:
        logger.exception(f"Draw {resp.calling} list failed")
        await finish_with_delete_msg(f"绘制{resp.calling}列表失败，请检查后台输出")

    ret = await matcher.send(MessageSegment.image(pic))
    msg_id = ret.get("message_id")
    if msg_id:
        state.setdefault(KEY_LIST_MSG_ID, []).append(msg_id)

    if reject:
        await matcher.reject()
    elif pause:
        await matcher.pause()


# endregion


# region search handlers


# handle
async def searcher_handler_1(matcher: Matcher, arg_msg: Message = CommandArg()):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)


# got
async def searcher_handler_2(
    matcher: Matcher,
    state: T_State,
    arg: str = ArgPlainText("arg"),
):
    keyword = arg.strip()
    if not keyword:
        await matcher.finish("消息无文本，放弃点播")

    searcher = cast(Type[BaseSearcher], state[KEY_SEARCHER_TYPE])(keyword)
    state[KEY_SEARCHER] = searcher


# handle
async def searcher_handler_3(matcher: Matcher, state: T_State):
    searcher: BaseSearcher = state[KEY_SEARCHER]
    calling = searcher.calling

    try:
        result = await searcher.search()
    except Exception:
        logger.exception(f"Search {calling} {searcher.keyword} failed")
        await matcher.finish(f"搜索{calling}失败，请检查后台输出")

    if not result:
        await matcher.finish(f"没搜到任何{calling}捏")

    if isinstance(result, BaseSong):
        await matcher.finish(await result.to_card_message())

    if isinstance(result, BaseSearcher):
        state[KEY_SEARCHER] = result
        await searcher_handler_3(matcher, state)
        return

    await send_search_resp(result)


# receive
async def searcher_handler_4(matcher: Matcher, event: MessageEvent, state: T_State):
    arg = event.get_message().extract_plain_text().strip().lower()

    if arg in EXIT_COMMAND:
        await finish_with_delete_msg("已退出选择")

    searcher: BaseSearcher = state[KEY_SEARCHER]

    if arg in PREVIOUS_COMMAND:
        try:
            resp = await searcher.prev_page()
        except ValueError:
            await matcher.reject("已经是第一页了")
        await send_search_resp(resp, reject=True)

    if arg in NEXT_COMMAND:
        try:
            resp = await searcher.next_page()
        except ValueError:
            await matcher.reject("已经是最后一页了")
        await send_search_resp(resp, reject=True)

    if arg.isdigit():
        try:
            song = await searcher.select(int(arg))
        except ValueError:
            await matcher.reject("序号输入有误，请重新输入")

        if isinstance(song, BaseSong):
            await finish_with_delete_msg(await song.to_card_message())
        else:  # BaseSearcher
            state[KEY_SEARCHER] = song
            await searcher_handler_3(matcher, state)
            await matcher.reject()

    if config.ncm_illegal_cmd_finish:
        await finish_with_delete_msg("非正确指令，已退出点歌")

    await matcher.reject("非正确指令，请重新输入\nTip: 你可以发送 `退出` 来退出点歌模式")


def register_search_handlers():
    for s in searchers:
        c_pri, *c_alias = s.commands
        cmd = on_command(c_pri, aliases=set(c_alias), state={KEY_SEARCHER_TYPE: s})
        cmd.handle()(searcher_handler_1)
        cmd.got("arg", "请发送搜索内容")(searcher_handler_2)
        cmd.handle()(searcher_handler_3)
        cmd.receive()(searcher_handler_4)


register_search_handlers()


# endregion
