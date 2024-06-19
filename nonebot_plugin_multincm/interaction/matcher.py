import asyncio
from typing import List, Type, Union, cast

from arclet.alconna import Alconna, Args, CommandMeta, Field
from cookit.loguru import logged_suppress
from cookit.nonebot.alconna import RecallContext
from nonebot import logger
from nonebot.adapters import Event as BaseEvent
from nonebot.exception import FinishedException
from nonebot.matcher import current_matcher
from nonebot.typing import T_State
from nonebot_plugin_alconna import AlconnaMatcher, on_alconna
from nonebot_plugin_alconna.uniseg import UniMessage
from nonebot_plugin_waiter import waiter

from ..config import config
from ..providers import (
    BaseSearcher,
    BaseSong,
    BaseSongList,
    GeneralSearcher,
    GeneralSongList,
    GeneralSongOrList,
    SongListInnerResp,
)
from ..render import render_list_resp
from .common import SEARCHER_COMMANDS, to_normal_msg
from .ob_v11 import is_ob_v11_ev, song_to_ob_v11_card_msg

KEY_SEARCHER = "searcher"

EXIT_COMMAND = (
    "退出", "tc", "取消", "qx", "quit", "q", "exit", "e", "cancel", "c", "0",
)  # fmt: skip
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")
JUMP_PAGE_PREFIX = ("page", "p", "跳页", "页")


async def plaintext_extractor(ev: BaseEvent) -> str:
    return ev.get_plaintext()


async def send_song(song: BaseSong):
    # event = current_event.get()
    matcher = cast(AlconnaMatcher, current_matcher.get())

    async def send_card() -> bool:
        if config.ncm_ob11_use_card and is_ob_v11_ev():
            with logged_suppress(f"Send {type(song).__name__} card failed"):
                await matcher.send(await song_to_ob_v11_card_msg(song))
                return True
        return False

    if not (await send_card()):
        await matcher.send(await to_normal_msg(song))

    # TODO: cache song
    # session_id = event.get_session_id()


async def searcher_handler_0(matcher: AlconnaMatcher, state: T_State, keyword: str):
    searcher: GeneralSongList = cast(Type[GeneralSearcher], state[KEY_SEARCHER])(
        keyword,
    )
    recall = RecallContext(delay=config.ncm_delete_list_msg_delay)

    async def handle_result(
        result: Union[GeneralSongOrList, List[SongListInnerResp], None],
    ):
        nonlocal searcher

        if result is None:
            await matcher.finish("没有搜索到任何内容")

        if isinstance(result, BaseSong):
            await send_song(result)
            await matcher.finish()

        if isinstance(result, BaseSongList):
            searcher = result
            return

        try:
            await recall.send(
                UniMessage.image(raw=await render_list_resp(searcher, result)),
            )
        except Exception:
            logger.exception(f"Failed to render {type(searcher).__name__} image")
            await matcher.finish("图片渲染失败，请检查后台输出")

        illegal_counter = 0
        async for msg in waiter(["message"], keep_session=True)(plaintext_extractor)(
            prompt=None,  # type: ignore
        ):
            if msg is None:
                await matcher.finish()
            msg = msg.strip().lower()

            if msg in EXIT_COMMAND:
                await matcher.finish("已退出选择")

            if msg in PREVIOUS_COMMAND:
                if searcher.is_first_page:
                    await recall.send("已经是第一页了")
                    continue
                searcher.current_page -= 1

            if msg in NEXT_COMMAND:
                if searcher.is_last_page:
                    await recall.send("已经是最后一页了")
                    continue
                searcher.current_page += 1

            if prefix := next((p for p in JUMP_PAGE_PREFIX if msg.startswith(p)), None):
                msg = msg[len(prefix) :].strip()
                if not (msg.isdigit() and searcher.page_valid(p := int(msg))):
                    await recall.send("页码输入有误，请重新输入")
                    continue
                searcher.current_page = p
                break

            if msg.isdigit():
                if not searcher.index_valid((index := int(msg) - 1)):
                    await recall.send("序号输入有误，请重新输入")
                    continue
                try:
                    resp = await searcher.select(index)
                except Exception:
                    logger.exception(
                        f"Error when selecting index {index} from {type(searcher).__name__}",
                    )
                    await matcher.finish("搜索出错，请检查后台输出")
                await handle_result(resp)
                return

            if config.ncm_illegal_cmd_finish:
                await matcher.finish("非正确指令，已退出选择")
            if illegal_counter >= config.ncm_illegal_cmd_limit:
                await matcher.finish("非法指令次数过多，已自动退出选择")
            await recall.send(
                "非正确指令，请重新输入\nTip: 你可以发送 `退出` 来退出点歌模式",
            )
            illegal_counter += 1

    while True:
        try:
            result = await searcher.get_page()
        except Exception:
            logger.exception(
                f"Error when using {type(searcher).__name__} to search {keyword}",
            )
            await matcher.send("搜索出错，请检查后台输出")
            break
        else:
            try:
                await handle_result(result)
            except FinishedException:
                break

    if config.ncm_delete_list_msg:
        asyncio.create_task(recall.recall())
    await matcher.finish()


def __register_searcher_matchers():
    def do_reg(searcher: Type[BaseSearcher], commands: List[str]):
        priv_cmd, *rest_cmds = commands
        calling = searcher.child_calling
        matcher = on_alconna(
            Alconna(
                priv_cmd,
                Args[
                    f"keyword#搜索关键词或{calling} ID",
                    str,
                    Field(completion=lambda: "请发送搜索内容"),
                ],
                separators="\n",
                meta=CommandMeta(
                    description=f"搜索{calling}。当输入{calling} ID 时会直接发送对应{calling}",
                ),
            ),
            aliases=set(rest_cmds),
            comp_config={"lite": True},
            use_cmd_start=True,
            default_state={KEY_SEARCHER: searcher},
        )
        matcher.handle()(searcher_handler_0)

    for k, v in SEARCHER_COMMANDS.items():
        do_reg(k, v)


__register_searcher_matchers()
