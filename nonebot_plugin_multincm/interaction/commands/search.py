import asyncio
from typing import Optional, Tuple, Type, cast

from cookit.loguru import warning_suppress
from cookit.nonebot.alconna import RecallContext
from nonebot import logger, on_command
from nonebot.adapters import Message as BaseMessage
from nonebot.matcher import Matcher, current_matcher
from nonebot.params import ArgPlainText, CommandArg, EventMessage
from nonebot.typing import T_State
from nonebot_plugin_alconna.uniseg import Reply, UniMessage, UniMsg
from nonebot_plugin_waiter import prompt

from ...config import config
from ...data_source import (
    BaseSearcher,
    BaseSong,
    GeneralGetPageReturn,
    GeneralSearcher,
    GeneralSongList,
    GeneralSongListPage,
    GeneralSongOrList,
    SongListPage,
    registered_searcher,
)
from ...render import render_list_resp
from ..message import construct_info_msg, send_song

KEY_SEARCHER = "searcher"
KEY_KEYWORD = "keyword"

EXIT_COMMAND = (
    "退出", "tc", "取消", "qx", "quit", "q", "exit", "e", "cancel", "c", "0",
)  # fmt: skip
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")
JUMP_PAGE_PREFIX = ("page", "p", "跳页", "页")


async def handle_song_or_list(
    result: GeneralSongOrList,
    matcher: Optional[Matcher] = None,
    send_init_info: bool = False,
):
    if not matcher:
        matcher = current_matcher.get()

    recall = RecallContext(delay=config.ncm_delete_msg_delay)

    async def handle(result: GeneralSongOrList) -> GeneralSongList:
        if isinstance(result, BaseSong):
            await send_song(result)
            await matcher.finish()
        return result

    async def select(
        song_list: GeneralSongList,
        result: GeneralSongListPage,
    ) -> GeneralSongList:
        try:
            await recall.send(UniMessage.image(raw=await render_list_resp(result)))
        except Exception:
            logger.exception(f"Failed to render page image for {result}")
            await matcher.finish("图片渲染失败，请检查后台输出")

        illegal_counter = 0

        async def tip_illegal(message: str):
            nonlocal illegal_counter
            illegal_counter += 1
            if config.ncm_illegal_cmd_limit and (
                illegal_counter >= config.ncm_illegal_cmd_limit
            ):
                await matcher.finish("非法指令次数过多，已自动退出选择")
            await recall.send(message)

        while True:
            msg = await prompt("")
            if msg is None:
                await matcher.finish()
            msg = msg.extract_plain_text().strip().lower()

            if msg in EXIT_COMMAND:
                await matcher.finish("已退出选择")

            if msg in PREVIOUS_COMMAND:
                if song_list.is_first_page:
                    await tip_illegal("已经是第一页了")
                    continue
                song_list.current_page -= 1
                return song_list

            if msg in NEXT_COMMAND:
                if song_list.is_last_page:
                    await tip_illegal("已经是最后一页了")
                    continue
                song_list.current_page += 1
                return song_list

            if prefix := next((p for p in JUMP_PAGE_PREFIX if msg.startswith(p)), None):
                msg = msg[len(prefix) :].strip()
                if not (msg.isdigit() and song_list.page_valid(p := int(msg))):
                    await tip_illegal("页码输入有误，请重新输入")
                    continue
                song_list.current_page = p
                return song_list

            if msg.isdigit():
                if not song_list.index_valid((index := int(msg) - 1)):
                    await tip_illegal("序号输入有误，请重新输入")
                    continue
                try:
                    resp = await song_list.select(index)
                except Exception:
                    logger.exception(
                        f"Error when selecting index {index} from {song_list}",
                    )
                    await matcher.finish("搜索出错，请检查后台输出")
                return await handle(resp)

            if config.ncm_illegal_cmd_finish:
                await matcher.finish("非正确指令，已退出选择")
            await tip_illegal(
                "非正确指令，请重新输入\nTip: 你可以发送 `退出` 来退出点歌模式",
            )

    async def handle_page(
        song_list: Optional[GeneralSongList],
        result: GeneralGetPageReturn,
    ) -> GeneralSongList:
        if result is None:
            await matcher.finish("没有搜索到任何内容")
        if isinstance(result, SongListPage):
            assert song_list
            return await select(song_list, result)
        return await handle(result)

    async def send_info(song_list: GeneralSongList):
        with warning_suppress(f"Failed to send info for {song_list}"):
            await recall.send(
                await construct_info_msg(song_list, tip_command=False),
            )

    async def main():
        song_list = await handle_page(None, result)
        if send_init_info:
            await send_info(song_list)
        while True:
            try:
                get_page_result = await song_list.get_page()
            except Exception:
                logger.exception(f"Error when using {song_list} to search")
                await matcher.finish("搜索出错，请检查后台输出")
            song_list = await handle_page(song_list, get_page_result)
            await send_info(song_list)

    try:
        await main()
    finally:
        if config.ncm_delete_msg:
            asyncio.create_task(recall.recall())


async def search_handler_0(
    matcher: Matcher,
    uni_msg: UniMsg,
    arg: BaseMessage = CommandArg(),
):
    arg_ok = arg.extract_plain_text().strip()
    if (
        (not arg_ok)
        and (Reply in uni_msg)
        and isinstance((r_raw := uni_msg[Reply, 0].msg), BaseMessage)
        and (r_raw.extract_plain_text().strip())
    ):
        arg = r_raw
        arg_ok = True
    if arg_ok:
        matcher.set_arg(KEY_KEYWORD, arg)
    else:
        await matcher.pause("请发送你要搜索的内容，或发送 0 退出搜索")


async def search_handler_1(matcher: Matcher, message: BaseMessage = EventMessage()):
    if matcher.get_arg(KEY_KEYWORD):
        return
    arg_str = message.extract_plain_text().strip()
    if arg_str in EXIT_COMMAND:
        await matcher.finish("已退出搜索")
    if not arg_str:
        await matcher.finish("输入无效，退出搜索")
    matcher.set_arg(KEY_KEYWORD, message)


async def search_handler_2(
    matcher: Matcher,
    state: T_State,
    keyword: str = ArgPlainText(KEY_KEYWORD),
):
    keyword = keyword.strip()
    searcher_type = cast(Type[GeneralSearcher], state[KEY_SEARCHER])
    searcher: GeneralSongList = searcher_type(keyword)
    await handle_song_or_list(searcher, matcher)


def __register_searcher_matchers():
    def do_reg(searcher: Type[BaseSearcher], commands: Tuple[str, ...]):
        priv_cmd, *rest_cmds = commands
        matcher = on_command(
            priv_cmd,
            aliases=set(rest_cmds),
            state={KEY_SEARCHER: searcher},
        )
        matcher.handle()(search_handler_0)
        matcher.handle()(search_handler_1)
        matcher.handle()(search_handler_2)

    for k, v in registered_searcher.items():
        do_reg(k, v)


__register_searcher_matchers()
