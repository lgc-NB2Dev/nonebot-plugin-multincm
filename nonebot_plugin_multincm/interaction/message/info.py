import asyncio as aio

from nonebot_plugin_alconna.uniseg import UniMessage

from ...data_source import BaseSong, GeneralSongOrList, Playlist, Voice
from ...utils import format_alias


async def construct_song_info_msg(
    it: BaseSong,
    tip_command: bool = True,
) -> UniMessage:
    info, url = await aio.gather(it.get_info(), it.get_url())
    alias = f"{format_alias('', info.alias)}\n" if info.alias else ""
    command_tip = "\n使用指令 `direct` 获取播放链接" if tip_command else ""
    return UniMessage.image(url=info.cover_url) + (
        f"{info.name}\n"
        f"{alias}"
        f"By: {info.display_artists}\n"
        f"{url}"
        f"{command_tip}"
    )


async def construct_voice_info_msg(
    it: Voice,
    tip_command: bool = True,
) -> UniMessage:
    info = it.info
    command_tip = "\n使用指令 `direct` 获取播放链接" if tip_command else ""
    return UniMessage.image(url=info.cover_url) + (
        f"{info.name}\n"
        f"电台：{info.radio.name}\n"
        f"台主：{info.dj.nickname}"
        f"{command_tip}"
    )


async def construct_playlist_info_msg(
    it: Playlist,
    tip_command: bool = True,
) -> UniMessage:
    info = it.info
    command_tip = "\n使用指令 `resolve` 选择歌单内容播放" if tip_command else ""
    return UniMessage.image(url=info.cover_img_url) + (
        f"{info.name}\n"
        f"创建者：{info.creator.nickname}\n"
        f"{await it.get_url()}"
        f"{command_tip}"
    )


async def construct_info_msg(
    it: GeneralSongOrList,
    tip_command: bool = True,
) -> UniMessage:
    type_map = {
        Playlist: construct_playlist_info_msg,
        Voice: construct_voice_info_msg,
        BaseSong: construct_song_info_msg,
    }
    return await next(
        (func(it, tip_command) for t, func in type_map.items() if isinstance(it, t)),
    )
