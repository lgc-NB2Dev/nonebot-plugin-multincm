import asyncio
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import (
    AsyncIterable,
    Dict,
    List,
    NoReturn,
    Optional,
    Protocol,
    Type,
    Union,
    cast,
)

from httpx import AsyncClient
from nonebot import logger, on_command, on_message
from nonebot.adapters.onebot.v11 import (
    ActionFailed,
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
    NetworkError,
    PrivateMessageEvent,
)
from nonebot.dependencies import Dependent
from nonebot.internal.adapter import Bot as BaseBot
from nonebot.internal.adapter import Event as BaseEvent
from nonebot.matcher import Matcher, current_bot, current_event, current_matcher
from nonebot.params import ArgPlainText, CommandArg
from nonebot.rule import Rule
from nonebot.typing import T_RuleChecker, T_State

from .config import config
from .draw import SearchResp, draw_search_res, str_to_pic
from .msg_cache import SongCache, chat_last_song_cache
from .providers import (
    BaseSearcher,
    BaseSearcherType,
    BaseSong,
    BaseSongType,
    searchers,
    songs,
)

KEY_SEARCHER_TYPE = "searcher_type"
KEY_SEARCHER = "searcher"
KEY_LIST_MSG_ID = "list_msg_id"

KEY_RESOLVED_URL = "resolved_url"
KEY_SEND_LINK = "send_link"
KEY_UPLOAD_FILE = "upload_file"
KEY_IS_AUTO_RESOLVE = "is_auto_resolve"

EXIT_COMMAND = ("退出", "tc", "取消", "qx", "quit", "q", "exit", "e", "cancel", "c", "0")
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")

SONG_LINK_TYPES_MAP = {s: s.link_types for s in songs}
LINK_TYPES = [t for s in songs for t in s.link_types]

_link_types_reg = "|".join(LINK_TYPES)
SONG_URL_REGEX = (
    rf"music\.163\.com/(.*?)(?P<type>{_link_types_reg})(/?\?id=|/)(?P<id>[0-9]+)&?"
)
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"


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


async def send_search_resp(resp: SearchResp):
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


async def cache_song(song: BaseSong, session: Optional[str] = None):
    if not session:
        session = current_event.get().get_session_id()
    chat_last_song_cache.set(session, SongCache(type(song), await song.get_id()))


async def send_song(song: BaseSong):
    matcher = current_matcher.get()

    try:
        await matcher.send(await song.to_card_message())
    except ActionFailed:
        logger.warning(f"Send {song.calling} card failed")

    await cache_song(song)


async def get_song_from_type(type_name: str) -> Type[BaseSongType]:
    if type_name not in LINK_TYPES:
        raise ValueError(f"Invalid type name: {type_name}")

    for song_cls, types in SONG_LINK_TYPES_MAP.items():
        if type_name in types:
            return song_cls

    raise RuntimeError  # should never reach here


async def build_cache_from_type(song_type: str, song_id: str) -> SongCache:
    song_cls = await get_song_from_type(song_type)
    return SongCache(song_cls, int(song_id))


class UrlResolveRes(Protocol):
    async def get(self) -> BaseSongType:
        ...


@dataclass
class ShortUrlResolveRes(UrlResolveRes):
    suffix: str

    async def get(self) -> BaseSongType:
        async with AsyncClient(base_url=SHORT_URL_BASE) as client:
            resp = await client.get(self.suffix, follow_redirects=False)

            if resp.status_code // 100 != 3:
                raise ValueError(
                    f"Short url {self.suffix} "
                    f"returned invalid status code {resp.status_code}",
                )

            location = resp.headers.get("Location")
            if not location:
                raise ValueError(f"Short url {self.suffix} returned no location header")

        matched = re.search(SONG_URL_REGEX, location, re.I)
        if not matched:
            raise ValueError(
                f"Location {location} of short url {self.suffix} is not a song url",
            )

        groups = matched.groupdict()
        cache = await build_cache_from_type(groups["type"], groups["id"])
        return await cache.get()


async def get_resolve_res(res: UrlResolveRes) -> BaseSongType:
    matcher = current_matcher.get()
    try:
        return await res.get()
    except ValueError as e:
        logger.warning(f"ValueError: {e}")
        await matcher.finish("链接无效")
    except Exception:
        logger.exception(f"Get UrlResolveRes {res} failed")
        await matcher.finish("解析失败，请检查后台输出")


async def upload_music(song: BaseSong):
    playable_url = await song.get_playable_url()
    logger.debug(playable_url)

    name, artists = await asyncio.gather(song.get_name(), song.get_artists())
    suffix = Path(playable_url).suffix
    file_name = f"[{song.calling}] {name} - {'、'.join(artists)}{suffix}"

    bot = cast(Bot, current_bot.get())
    download_ret: Dict[str, str] = await bot.download_file(url=playable_url)
    file_path = download_ret["file"]

    event = cast(Union[PrivateMessageEvent, GroupMessageEvent], current_event.get())
    if isinstance(event, PrivateMessageEvent):
        await bot.upload_private_file(
            user_id=event.user_id,
            file=file_path,
            name=file_name,
        )
        return

    folder_id = None
    if folder_name := config.ncm_upload_folder_name:
        file_list_ret: Dict = await bot.get_group_root_files(group_id=event.group_id)
        folder_id = next(
            (
                x["folder_id"]
                for x in (file_list_ret["folders"] or [])
                if x["folder_name"] == folder_name
            ),
            None,
        )
        if not folder_id:
            try:
                await bot.create_group_file_folder(
                    group_id=event.group_id,
                    name=folder_name,
                    parent_id="/",
                )
                files = await bot.get_group_root_files(group_id=event.group_id)
                folder_id = next(
                    x["folder_id"]
                    for x in files["folders"]
                    if x["folder_name"] == folder_name
                )
            except ActionFailed as e:
                logger.warning(
                    f"Create group file folder {folder_name} failed: {e}",
                )

    await bot.upload_group_file(
        group_id=event.group_id,
        file=file_path,
        name=file_name,
        folder=folder_id,
    )


# endregion


# region rules


class SequentialRule:
    def __init__(
        self,
        *checkers: Union[T_RuleChecker, Dependent[bool]],
        is_all: bool = False,
    ) -> None:
        self.checkers: List[Union[SequentialRule, Rule]] = [
            (checker if isinstance(checker, (SequentialRule, Rule)) else Rule(checker))
            for checker in checkers
        ]
        self.is_all: bool = is_all

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{', '.join(f'{x!r}' for x in self.checkers)}, "
            f"is_all={self.is_all})"
        )

    async def __call__(self, bot: BaseBot, event: BaseEvent, state: T_State) -> bool:
        async def async_all(iterable: AsyncIterable[bool]) -> bool:
            async for i in iterable:
                if not i:
                    return False
            return True

        async def async_any(iterable: AsyncIterable[bool]) -> bool:
            async for i in iterable:
                if i:
                    return True
            return False

        async def check() -> AsyncIterable[bool]:
            for checker in self.checkers:
                resp = await checker(bot=bot, event=event, state=state)
                yield bool(resp)

        judge_func = async_all if self.is_all else async_any
        return await judge_func(check())

    def __and__(self, other: Union[T_RuleChecker, Rule, None]) -> "SequentialRule":
        if not other:
            return self
        return SequentialRule(*self.checkers, other, is_all=self.is_all)

    def __rand__(self, other: Union[T_RuleChecker, Rule, None]) -> "SequentialRule":
        if not other:
            return self
        return SequentialRule(other, *self.checkers, is_all=self.is_all)


async def resolve_music_from_msg(
    message: Message,
    resolve_playable_card: bool = True,
) -> Optional[UrlResolveRes]:
    card = next(iter(message["json"]), None)
    if card:
        msg_str = card.data["data"]
        is_playable_card = '"musicUrl"' in msg_str
        if (not resolve_playable_card) and is_playable_card:
            return None
    else:
        msg_str = message.extract_plain_text()

    matched = None
    for regex in (SONG_URL_REGEX, SHORT_URL_REGEX):
        if matched := re.search(regex, msg_str, re.I):
            break
    if not matched:
        return None

    groups = matched.groupdict()
    if "suffix" in groups:
        return ShortUrlResolveRes(groups["suffix"])
    return await build_cache_from_type(groups["type"], groups["id"])


async def rule_music_msg(event: MessageEvent, state: T_State) -> bool:
    message = event.reply.message if event.reply else event.message
    if res := await resolve_music_from_msg(message):
        state[KEY_RESOLVED_URL] = res
    return bool(res)


async def rule_chat_last_music(event: MessageEvent, state: T_State) -> bool:
    if cache := chat_last_song_cache.get(event.get_session_id()):
        state[KEY_RESOLVED_URL] = cache
    return bool(cache)


async def rule_auto_resolve(event: MessageEvent, state: T_State) -> bool:
    if not config.ncm_auto_resolve:
        return False
    if res := await resolve_music_from_msg(
        event.message,
        config.ncm_resolve_playable_card,
    ):
        state[KEY_RESOLVED_URL] = res
    return bool(res)


rule_has_music_msg = SequentialRule(
    rule_music_msg,
    rule_chat_last_music,
    is_all=False,
)


# endregion


# region search handlers


async def search_handle_extract_arg(matcher: Matcher, arg_msg: Message = CommandArg()):
    if arg_msg.extract_plain_text().strip():
        matcher.set_arg("arg", arg_msg)


async def search_got_arg(
    matcher: Matcher,
    state: T_State,
    arg: str = ArgPlainText("arg"),
):
    keyword = arg.strip()
    if not keyword:
        await matcher.finish("消息无文本，放弃搜索")

    searcher = cast(Type[BaseSearcher], state[KEY_SEARCHER_TYPE])(keyword)
    state[KEY_SEARCHER] = searcher


async def search_handle_search(matcher: Matcher, state: T_State):
    searcher: BaseSearcher = state[KEY_SEARCHER]
    calling = searcher.calling

    try:
        result = await searcher.search()
    except Exception:
        logger.exception(f"Search {calling} `{searcher.keyword}` failed")
        await matcher.finish(f"搜索{calling}失败，请检查后台输出")

    if not result:
        await matcher.finish(f"没搜到任何{calling}捏")

    if isinstance(result, BaseSong):
        await send_song(result)
        await matcher.finish()

    if isinstance(result, BaseSearcher):
        state[KEY_SEARCHER] = result
        await search_handle_search(matcher, state)
        return

    await send_search_resp(result)


async def search_receive_select(matcher: Matcher, event: MessageEvent, state: T_State):
    arg = event.get_message().extract_plain_text().strip().lower()

    if arg in EXIT_COMMAND:
        await finish_with_delete_msg("已退出选择")

    searcher: BaseSearcherType = state[KEY_SEARCHER]

    if arg in PREVIOUS_COMMAND:
        try:
            resp = await searcher.prev_page()
        except ValueError:
            await matcher.reject("已经是第一页了")
        await send_search_resp(resp)
        await matcher.reject()

    if arg in NEXT_COMMAND:
        try:
            resp = await searcher.next_page()
        except ValueError:
            await matcher.reject("已经是最后一页了")
        await send_search_resp(resp)
        await matcher.reject()

    if arg.isdigit():
        try:
            song = await searcher.select(int(arg))
        except ValueError:
            await matcher.reject("序号输入有误，请重新输入")

        if isinstance(song, BaseSong):
            await send_song(song)
            await finish_with_delete_msg()

        # else:  # BaseSearcher
        state[KEY_SEARCHER] = song
        await search_handle_search(matcher, state)
        await matcher.reject()

    if config.ncm_illegal_cmd_finish:
        await finish_with_delete_msg("非正确指令，已退出点歌")

    await matcher.reject("非正确指令，请重新输入\nTip: 你可以发送 `退出` 来退出点歌模式")


def register_search_handlers():
    for s in searchers:
        c_pri, *c_alias = s.commands
        cmd = on_command(c_pri, aliases=set(c_alias), state={KEY_SEARCHER_TYPE: s})
        cmd.handle()(search_handle_extract_arg)
        cmd.got("arg", "请发送搜索内容")(search_got_arg)
        cmd.handle()(search_handle_search)
        cmd.receive()(search_receive_select)


register_search_handlers()


# endregion


# region resolve handlers


cmd_resolve = on_command(
    "解析",
    aliases={"resolve", "parse", "get"},
    rule=rule_has_music_msg,
)
cmd_resolve_url = on_command(
    "直链",
    aliases={"direct"},
    rule=rule_has_music_msg,
    state={KEY_SEND_LINK: True},
)
cmd_resolve_file = on_command(
    "上传",
    aliases={"upload"},
    rule=rule_has_music_msg,
    state={KEY_UPLOAD_FILE: True},
)
cmd_auto_resolve = on_message(
    rule=rule_auto_resolve,
    state={KEY_IS_AUTO_RESOLVE: True},
)


@cmd_resolve.handle()
@cmd_resolve_url.handle()
@cmd_resolve_file.handle()
@cmd_auto_resolve.handle()
async def _(matcher: Matcher, state: T_State):
    if KEY_IS_AUTO_RESOLVE in state:
        await matcher.send("检测到您发送了网易云音乐卡片/链接，正在为您解析")

    cache: SongCache = state[KEY_RESOLVED_URL]
    song = await get_resolve_res(cache)

    if KEY_SEND_LINK in state:
        await matcher.finish(await song.get_playable_url())

    if KEY_UPLOAD_FILE in state:
        await matcher.send("正在下载并上传音乐，需要的时间可能较长，请耐心等待")
        try:
            await upload_music(song)

        except Exception as e:
            logger.exception(f"Upload {song.calling} {await song.get_id()} failed")
            if isinstance(e, NetworkError):
                await matcher.finish(
                    f"上传{song.calling}失败，可能是下载或上传超时！请尝试调高 API_TIMEOUT 配置",
                )
            if isinstance(e, ActionFailed):
                await matcher.finish(
                    f"上传{song.calling}失败，可能是下载文件出错或无权限上传文件！请检查后台输出",
                )
            await matcher.finish(f"上传{song.calling}失败，请检查后台输出")

        else:
            await matcher.finish()

    await send_song(song)


# endregion


# region lyric handlers


cmd_get_lrc = on_command(
    "歌词",
    aliases={"lrc", "lyric", "lyrics"},
    rule=rule_has_music_msg,
)


@cmd_get_lrc.handle()
async def _(matcher: Matcher, state: T_State):
    cache: SongCache = state[KEY_RESOLVED_URL]
    song = await get_resolve_res(cache)

    try:
        lrc = await song.get_lyric()
    except Exception:
        logger.exception(f"Get {song.calling} {await song.get_id()} lyric failed")
        await matcher.finish(f"获取{song.calling}歌词失败，请检查后台输出")

    if not lrc:
        await matcher.finish("暂无歌词")

    pic = await str_to_pic(lrc)
    await matcher.finish(MessageSegment.image(pic))


# endregion
