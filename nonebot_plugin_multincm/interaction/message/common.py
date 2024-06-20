import asyncio as aio

from nonebot_plugin_alconna.uniseg import UniMessage

from ...providers import BaseSong, GeneralSongOrList, Playlist, Voice


async def construct_song_msg(it: BaseSong) -> UniMessage:
    name, artists, cover_url = await aio.gather(
        it.get_name(),
        it.get_artists(),
        it.get_cover_url(),
    )
    content = "、".join(artists)
    return UniMessage.image(url=cover_url) + (
        f"{name}\nBy: {content}\n使用指令 `direct` 获取播放链接"
    )


async def construct_voice_msg(it: Voice) -> UniMessage:
    info = it.info
    return UniMessage.image(url=info.cover_url) + (
        f"{info.name}\n"
        f"电台：{info.radio.name}\n"
        f"台主：{info.dj.nickname}\n"
        f"使用指令 `direct` 获取播放链接"
    )


async def construct_playlist_msg(it: Playlist) -> UniMessage:
    info = it.info
    return UniMessage.image(url=info.cover_img_url) + (
        f"{info.name}\n"
        f"创建者：{info.creator.nickname}\n"
        f"{await it.get_url()}\n"
        f"使用指令 `resolve` 选择内容播放"
    )


async def construct_result_msg(it: GeneralSongOrList) -> UniMessage:
    type_map = {
        Playlist: construct_playlist_msg,
        Voice: construct_voice_msg,
        BaseSong: construct_song_msg,
    }
    return await next((func(it) for t, func in type_map.items() if isinstance(it, t)))
