import asyncio
from contextlib import suppress
from typing import Tuple, Type, cast

from cookit.loguru import logged_suppress
from cookit.nonebot.alconna import RecallContext
from nonebot import logger, on_command
from nonebot.adapters import Message as BaseMessage
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher, current_matcher
from nonebot.params import CommandArg
from nonebot.typing import T_State
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_waiter import prompt

from ...config import config
from ...data_source import (
    BaseSearcher,
    BaseSong,
    BaseSongList,
    GeneralGetPageReturn,
    GeneralSearcher,
    GeneralSongList,
    GeneralSongListPage,
    registered_searcher,
)
from ...render import render_list_resp
from ..cache import set_cache
from ..message import construct_result_msg, get_card_sendable_ev_type, get_song_card_msg

KEY_SEARCHER = "searcher"

EXIT_COMMAND = (
    "退出", "tc", "取消", "qx", "quit", "q", "exit", "e", "cancel", "c", "0",
)  # fmt: skip
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")
JUMP_PAGE_PREFIX = ("page", "p", "跳页", "页")


async def send_song(song: BaseSong):
    async def send():
        matcher = current_matcher.get()

        if config.ncm_use_card:
            ev_type = None
            with suppress(TypeError):
                ev_type = get_card_sendable_ev_type()
            if ev_type:
                with logged_suppress(
                    f"Send {type(song).__name__} {song.id} card failed",
                ):
                    await matcher.send(await get_song_card_msg(song, ev_type))
                    return

        await (await construct_result_msg(song)).send()

    await send()
    await set_cache(song)


async def search_handler(
    matcher: Matcher,
    state: T_State,
    arg: BaseMessage = CommandArg(),
):
    keyword = arg.extract_plain_text().strip()
    searcher: GeneralSongList = cast(Type[GeneralSearcher], state[KEY_SEARCHER])(
        keyword,
    )
    recall = RecallContext(delay=config.ncm_delete_msg_delay)

    async def select_result(result: GeneralSongListPage):
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
                if searcher.is_first_page:
                    await tip_illegal("已经是第一页了")
                    continue
                searcher.current_page -= 1
                break

            if msg in NEXT_COMMAND:
                if searcher.is_last_page:
                    await tip_illegal("已经是最后一页了")
                    continue
                searcher.current_page += 1
                break

            if prefix := next((p for p in JUMP_PAGE_PREFIX if msg.startswith(p)), None):
                msg = msg[len(prefix) :].strip()
                if not (msg.isdigit() and searcher.page_valid(p := int(msg))):
                    await tip_illegal("页码输入有误，请重新输入")
                    continue
                searcher.current_page = p
                break

            if msg.isdigit():
                if not searcher.index_valid((index := int(msg) - 1)):
                    await tip_illegal("序号输入有误，请重新输入")
                    continue
                try:
                    resp = await searcher.select(index)
                except Exception:
                    logger.exception(
                        f"Error when selecting index {index} from {searcher}",
                    )
                    await matcher.finish("搜索出错，请检查后台输出")
                await handle_result(resp)
                break

            if config.ncm_illegal_cmd_finish:
                await matcher.finish("非正确指令，已退出选择")
            await tip_illegal(
                "非正确指令，请重新输入\nTip: 你可以发送 `退出` 来退出点歌模式",
            )

    async def handle_result(result: GeneralGetPageReturn):
        nonlocal searcher

        if result is None:
            await matcher.finish("没有搜索到任何内容")

        if isinstance(result, BaseSong):
            await send_song(result)
            await matcher.finish()

        if isinstance(result, BaseSongList):
            searcher = result
            return

        await select_result(result)

    while True:
        try:
            result = await searcher.get_page()
        except Exception:
            logger.exception(f"Error when using {searcher} to search")
            await matcher.send("搜索出错，请检查后台输出")
            break
        try:
            await handle_result(result)
        except FinishedException:
            break

    if config.ncm_delete_msg:
        asyncio.create_task(recall.recall())
    await matcher.finish()


def __register_searcher_matchers():
    def do_reg(searcher: Type[BaseSearcher], commands: Tuple[str, ...]):
        priv_cmd, *rest_cmds = commands
        matcher = on_command(
            priv_cmd,
            aliases=set(rest_cmds),
            state={KEY_SEARCHER: searcher},
        )
        matcher.handle()(search_handler)

    for k, v in registered_searcher.items():
        do_reg(k, v)


__register_searcher_matchers()
