import asyncio
import random
import re
from pathlib import Path
from typing import Dict, List, NoReturn, Optional, Type, Union, cast
from typing_extensions import Annotated

from httpx import AsyncClient
from nonebot import logger, on_command, on_regex
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
from nonebot.consts import REGEX_MATCHED
from nonebot.matcher import Matcher, current_bot, current_event, current_matcher
from nonebot.params import ArgPlainText, CommandArg, Depends
from nonebot.typing import T_State

from .config import config
from .draw import TablePage, draw_table_page, str_to_pic
from .msg_cache import SongCache, chat_last_song_cache
from .providers import BasePlaylist, BaseSearcher, BaseSong, playlists, searchers, songs

KEY_SEARCHER_TYPE = "searcher_type"
KEY_PLAYLIST = "playlist"
KEY_LIST_MSG_ID = "list_msg_id"

KEY_RESOLVE = "resolve"
KEY_SEND_LINK = "send_link"
KEY_UPLOAD_FILE = "upload_file"
KEY_SEND_RECORD = "send_record"
KEY_IS_AUTO_RESOLVE = "is_auto_resolve"
KEY_ILLEGAL_COUNT = "illegal_count"

EXIT_COMMAND = (
    "退出",
    "tc",
    "取消",
    "qx",
    "quit",
    "q",
    "exit",
    "e",
    "cancel",
    "c",
    "0",
)
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")
JUMP_PAGE_PREFIX = ("page", "p", "跳页", "页")

LINK_TYPES_MAP = {s: s.link_types for s in (*songs, *playlists)}
LINK_TYPES = [t for s in (*songs, *playlists) for t in s.link_types]

_link_types_reg = "|".join(LINK_TYPES)
URL_REGEX = (
    rf"music\.163\.com/(.*?)(?P<type>{_link_types_reg})(/?\?id=|/)(?P<id>[0-9]+)&?"
)
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"

SongOrPlaylist = Union[BaseSong, BasePlaylist]

# region util funcs


async def delete_list_msg(msg_id: List[int], bot: Bot):
    for i in msg_id:
        await asyncio.sleep(random.uniform(*config.ncm_delete_list_msg_delay))
        try:
            await bot.delete_msg(message_id=i)
        except Exception as e:
            logger.warning(f"撤回消息 {i} 失败: {e!r}")


async def finish_with_delete_msg(
    msg: Optional[Union[str, MessageSegment, Message]] = None,
) -> NoReturn:
    matcher = current_matcher.get()
    msg_id = matcher.state.get(KEY_LIST_MSG_ID)

    if config.ncm_delete_list_msg and msg_id:
        bot = cast(Bot, current_bot.get())
        asyncio.create_task(delete_list_msg(msg_id, bot))

    await matcher.finish(msg)


async def send_table_page(resp: TablePage):
    matcher = current_matcher.get()
    state = matcher.state

    try:
        pic = await draw_table_page(resp)
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
    chat_last_song_cache.set(session, SongCache(type(song), song.song_id))


async def send_song(song: BaseSong):
    matcher = current_matcher.get()

    try:
        await matcher.send(await song.to_card_message())
    except ActionFailed:
        logger.warning(f"Send {song.calling} card failed")

    await cache_song(song)


async def get_class_from_link_type(type_name: str) -> Type[SongOrPlaylist]:
    if type_name not in LINK_TYPES:
        raise ValueError(f"Invalid type name: {type_name}")

    for kls, types in LINK_TYPES_MAP.items():
        if type_name in types:
            return kls

    raise RuntimeError  # should never reach here


async def resolve_short_url(suffix: str) -> SongOrPlaylist:
    async with AsyncClient(base_url=SHORT_URL_BASE) as client:
        resp = await client.get(suffix, follow_redirects=False)

        if resp.status_code // 100 != 3:
            raise ValueError(
                f"Short url {suffix} "
                f"returned invalid status code {resp.status_code}",
            )

        location = resp.headers.get("Location")
        if not location:
            raise ValueError(f"Short url {suffix} returned no location header")

    matched = re.search(URL_REGEX, location, re.IGNORECASE)
    if not matched:
        raise ValueError(
            f"Location {location} of short url {suffix} is not a song url",
        )

    groups = matched.groupdict()
    type_name = groups["type"]
    arg_id = groups["id"]
    kls = await get_class_from_link_type(type_name)
    return await kls.from_id(int(arg_id))


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


async def illegal_finish():
    if config.ncm_illegal_cmd_finish:
        await finish_with_delete_msg("非正确指令，已退出点歌")
    if config.ncm_illegal_cmd_limit <= 0:
        return
    state = current_matcher.get().state
    count = state.get(KEY_ILLEGAL_COUNT, 0) + 1
    if count >= config.ncm_illegal_cmd_limit:
        await finish_with_delete_msg("非法指令次数过多，已自动退出点歌")
    state[KEY_ILLEGAL_COUNT] = count


# endregion


# region dependencies & rules
# 怎么感觉越写越花了，写得自己像个傻逼


async def resolve_song_or_playlist_from_msg(
    matcher: Matcher,
    event: MessageEvent,
    matched: Optional[re.Match] = None,
) -> Optional[SongOrPlaylist]:
    is_auto_resolve = bool(matched)
    message = (
        event.reply.message
        if ((not is_auto_resolve) and event.reply)
        else event.message
    )
    resolve_playable_card = (
        config.ncm_resolve_playable_card if is_auto_resolve else True
    )

    card = next(iter(message["json"]), None)
    if card:
        msg_str = card.data["data"]
        is_playable_card = '"musicUrl"' in msg_str
        if (not resolve_playable_card) and is_playable_card:
            return None
    else:
        msg_str = message.extract_plain_text()

    if not matched:
        for regex in (URL_REGEX, SHORT_URL_REGEX):
            if matched := re.search(regex, msg_str, re.IGNORECASE):
                break
        if not matched:
            return None

    if is_auto_resolve:
        await matcher.send("检测到您发送了网易云音乐卡片/链接，正在为您解析")

    groups = matched.groupdict()
    if "suffix" in groups:
        suffix = groups["suffix"]
        try:
            return await resolve_short_url(suffix)
        except ValueError as e:
            logger.error(f"Invalid short url {suffix}: {e}")
            await matcher.finish("短链无效")
        except Exception:
            logger.exception(f"Resolve short url {suffix} failed")
            await matcher.finish("解析短链失败，请检查后台输出")

    type_name = groups["type"]
    arg_id = groups["id"]

    kls = await get_class_from_link_type(type_name)
    try:
        return await kls.from_id(int(arg_id))
    except Exception:
        logger.exception(f"Resolve {type_name} {arg_id} failed")
        await matcher.finish(f"获取{kls.calling}失败，请检查后台输出")


async def dependency_resolve_song_or_playlist(
    matcher: Matcher,
    event: MessageEvent,
    state: T_State,
) -> SongOrPlaylist:
    is_auto_resolve: bool = state.get(KEY_IS_AUTO_RESOLVE, False)
    if is_auto_resolve and (not config.ncm_auto_resolve):
        await matcher.finish()

    if song := await resolve_song_or_playlist_from_msg(
        matcher,
        event,
        state.get(REGEX_MATCHED) if is_auto_resolve else None,
    ):
        return song

    if (not is_auto_resolve) and (
        cache := chat_last_song_cache.get(event.get_session_id())
    ):
        try:
            return await cache.get()
        except Exception:
            logger.exception(f"Get {cache} failed")
            await matcher.finish(f"获取{cache.song_class.calling}失败，请检查后台输出")

    return await matcher.finish()


ResolvedSongOrPlaylist = Annotated[
    SongOrPlaylist,
    Depends(dependency_resolve_song_or_playlist, use_cache=False),
]


# endregion


# region search handlers


async def handle_get_page(
    result: Union[TablePage, SongOrPlaylist, None],
    calling: str,
):
    matcher = current_matcher.get()
    state = matcher.state

    if not result:
        await matcher.finish(f"没搜到任何{calling}捏")

    if isinstance(result, BaseSong):
        await send_song(result)
        await matcher.finish()

    if isinstance(result, BasePlaylist):
        state[KEY_PLAYLIST] = result
        await search_handle_search(matcher, state)

    else:
        await send_table_page(result)


async def search_handle_extract_arg(
    matcher: Matcher,
    event: MessageEvent,
    arg_msg: Message = CommandArg(),
):
    if event.reply:
        arg_msg = event.reply.message
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
    if keyword in EXIT_COMMAND:
        await matcher.finish("已退出搜索")

    searcher = cast(Type[BaseSearcher], state[KEY_SEARCHER_TYPE])(keyword)
    state[KEY_PLAYLIST] = searcher


async def search_handle_search(matcher: Matcher, state: T_State):
    playlist: BasePlaylist = state[KEY_PLAYLIST]
    calling = playlist.child_calling

    try:
        result = cast(
            Union[TablePage, SongOrPlaylist, None],
            await playlist.get_page(),
        )
    except Exception:
        logger.exception(f"Failed to call get_page() of {playlist}")
        if isinstance(playlist, BaseSearcher):
            await matcher.finish(f"搜索{calling}失败，请检查后台输出")
        else:
            await matcher.finish(f"获取{calling}列表失败，请检查后台输出")

    await handle_get_page(result, calling)


async def search_receive_select(matcher: Matcher, event: MessageEvent, state: T_State):
    arg = event.get_message().extract_plain_text().strip().lower()

    if arg in EXIT_COMMAND:
        await finish_with_delete_msg("已退出选择")

    playlist: BasePlaylist = state[KEY_PLAYLIST]

    def reset_illegal():
        state[KEY_ILLEGAL_COUNT] = 0

    if arg in PREVIOUS_COMMAND:
        reset_illegal()
        try:
            resp = await playlist.prev_page()
        except ValueError:
            await matcher.reject("已经是第一页了")
        await send_table_page(resp)
        await matcher.reject()

    if arg in NEXT_COMMAND:
        reset_illegal()
        try:
            resp = await playlist.next_page()
        except ValueError:
            await matcher.reject("已经是最后一页了")
        await send_table_page(resp)
        await matcher.reject()

    if prefix := next((p for p in JUMP_PAGE_PREFIX if arg.startswith(p)), None):
        arg = arg[len(prefix) :].strip()
        if not arg.isdigit():
            await illegal_finish()
            await matcher.reject("页码输入有误，请重新输入")

        try:
            resp = cast(
                Union[TablePage, SongOrPlaylist, None],
                await playlist.get_page(int(arg)),
            )
        except ValueError:
            await illegal_finish()
            await matcher.reject("页码输入有误，请重新输入")

        reset_illegal()
        await handle_get_page(resp, playlist.calling)
        await matcher.reject()

    if arg.isdigit():
        try:
            result = cast(SongOrPlaylist, await playlist.select(int(arg)))
        except ValueError:
            await illegal_finish()
            await matcher.reject("序号输入有误，请重新输入")

        reset_illegal()
        if isinstance(result, BaseSong):
            await send_song(result)
            await finish_with_delete_msg()

        # else:  # BasePlaylist
        state[KEY_PLAYLIST] = result
        await search_handle_search(matcher, state)
        await matcher.reject()

    await illegal_finish()
    await matcher.reject(
        "非正确指令，请重新输入\nTip: 你可以发送 `退出` 来退出点歌模式",
    )


def append_playlist_handlers(matcher: Type[Matcher]):
    matcher.handle()(search_handle_search)
    matcher.receive()(search_receive_select)


def register_search_handlers():
    def reg_one(s: Type[BaseSearcher]):
        c_pri, *c_alias = s.commands
        cmd = on_command(c_pri, aliases=set(c_alias), state={KEY_SEARCHER_TYPE: s})
        cmd.handle()(search_handle_extract_arg)
        cmd.got("arg", "请发送搜索内容，发送 0 退出搜索")(search_got_arg)
        append_playlist_handlers(cmd)

    for s in searchers:
        reg_one(s)


register_search_handlers()


# endregion


# region resolve handlers


cmd_resolve = on_command(
    "解析",
    aliases={"resolve", "parse", "get"},
    state={KEY_RESOLVE: True},
)
cmd_resolve_url = on_command(
    "直链",
    aliases={"direct"},
    state={KEY_SEND_LINK: True},
)
cmd_resolve_file = on_command(
    "上传",
    aliases={"upload"},
    state={KEY_UPLOAD_FILE: True},
)
cmd_send_record = on_command(
    "语音",
    aliases={"record"},
    state={KEY_SEND_RECORD: True},
)
cmd_auto_resolve = on_regex(
    URL_REGEX,
    state={KEY_RESOLVE: True, KEY_IS_AUTO_RESOLVE: True},
)
cmd_auto_resolve_short = on_regex(
    SHORT_URL_REGEX,
    state={KEY_RESOLVE: True, KEY_IS_AUTO_RESOLVE: True},
)


@cmd_resolve.handle()
@cmd_resolve_url.handle()
@cmd_resolve_file.handle()
@cmd_send_record.handle()
@cmd_auto_resolve.handle()
@cmd_auto_resolve_short.handle()
async def _(matcher: Matcher, state: T_State, resolved: ResolvedSongOrPlaylist):
    if KEY_RESOLVE in state:
        if isinstance(resolved, BasePlaylist):
            state[KEY_PLAYLIST] = resolved
            return
        await send_song(resolved)

    if not isinstance(resolved, BaseSong):
        await matcher.finish(f"{resolved.calling}不支持此操作")

    if KEY_SEND_LINK in state:
        await matcher.finish(await resolved.get_playable_url())

    elif KEY_UPLOAD_FILE in state:
        await matcher.send(
            f"正在下载并上传{resolved.calling}，需要的时间可能较长，请耐心等待",
        )
        try:
            await upload_music(resolved)

        except Exception as e:
            logger.exception(f"Upload {resolved.calling} {resolved.song_id} failed")
            if isinstance(e, NetworkError):
                await matcher.finish(
                    f"上传{resolved.calling}失败，可能是下载或上传超时！请尝试调高 API_TIMEOUT 配置",
                )
            if isinstance(e, ActionFailed):
                await matcher.finish(
                    f"上传{resolved.calling}失败，可能是下载/上传文件出错或无权限上传文件！\n{e}",
                )
            await matcher.finish(
                f"上传{resolved.calling}失败，遇到未知错误，请检查后台输出",
            )

    elif KEY_SEND_RECORD in state and config.ncm_enable_record:
        await matcher.send(MessageSegment.record(await resolved.get_playable_url()))

    await matcher.finish()


def append_searcher_handlers_to_resolve():
    def once(m: Type[Matcher]):
        append_playlist_handlers(m)

    for m in (cmd_resolve, cmd_auto_resolve):
        once(m)


append_searcher_handlers_to_resolve()


# endregion


# region lyric handlers


cmd_get_lrc = on_command(
    "歌词",
    aliases={"lrc", "lyric", "lyrics"},
)


@cmd_get_lrc.handle()
async def _(matcher: Matcher, resolved: ResolvedSongOrPlaylist):
    if not isinstance(resolved, BaseSong):
        await matcher.finish(f"{resolved.calling}不支持此操作")

    try:
        lrc = await resolved.get_lyric()
    except Exception:
        logger.exception(f"Get {resolved.calling} {resolved.song_id} lyric failed")
        await matcher.finish(f"获取{resolved.calling}歌词失败，请检查后台输出")

    if not lrc:
        await matcher.finish("暂无歌词")

    pic = await str_to_pic(lrc)
    await matcher.finish(MessageSegment.image(pic))


# endregion
