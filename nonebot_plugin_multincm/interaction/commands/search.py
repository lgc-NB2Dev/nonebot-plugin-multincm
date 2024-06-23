import asyncio
from contextlib import suppress
from typing import Any, Optional, Tuple, Type, cast

from cookit.nonebot.alconna import RecallContext
from nonebot import logger, on_command, on_regex
from nonebot.adapters import Message as BaseMessage
from nonebot.consts import REGEX_MATCHED
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher, current_matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.typing import T_State
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_waiter import prompt

from nonebot_plugin_multincm.data_source.base import BaseSongList

from ...config import config
from ...const import SHORT_URL_REGEX, URL_REGEX
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
from ..message import send_song
from ..resolver import ResolvedItem

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

    async def main():
        song_list = await handle_page(None, result)
        while True:
            try:
                get_page_result = await song_list.get_page()
            except Exception:
                logger.exception(f"Error when using {song_list} to search")
                await matcher.finish("搜索出错，请检查后台输出")
            song_list = await handle_page(song_list, get_page_result)

    with suppress(FinishedException):
        await main()

    if config.ncm_delete_msg:
        asyncio.create_task(recall.recall())
    await matcher.finish()


async def search_handler_0(matcher: Matcher, arg: BaseMessage = CommandArg()):
    if arg.extract_plain_text().strip():
        matcher.set_arg(KEY_KEYWORD, arg)


async def search_handler_1(
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
        matcher.got(KEY_KEYWORD, "请发送你要搜索的内容")(search_handler_1)

    for k, v in registered_searcher.items():
        do_reg(k, v)


async def resolve_handler(matcher: Matcher, state: T_State, result: ResolvedItem):
    regex_matched = state.get(REGEX_MATCHED)
    if regex_matched and isinstance(result, BaseSongList):
        return
    await handle_song_or_list(cast(Any, result), matcher)


def __register_resolve_matchers():
    matcher = on_command("解析", aliases={"resolve", "parse", "get"})
    matcher.handle()(resolve_handler)
    if config.ncm_auto_resolve:
        reg_matcher = on_regex(URL_REGEX)
        reg_matcher.handle()(resolve_handler)
        reg_short_matcher = on_regex(SHORT_URL_REGEX)
        reg_short_matcher.handle()(resolve_handler)


__register_searcher_matchers()
__register_resolve_matchers()