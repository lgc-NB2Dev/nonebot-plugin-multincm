import asyncio as aio
from typing import Dict, List, Type, Union
from typing_extensions import TypeAlias

from nonebot_plugin_alconna.uniseg import UniMessage

from ..providers import (
    BasePlaylist,
    BaseSearcher,
    BaseSong,
    Playlist,
    PlaylistSearcher,
    Song,
    SongSearcher,
    Voice,
    VoiceSearcher,
)

TSongOrPlaylist: TypeAlias = Union[BaseSong, BasePlaylist]
TSongOrPlaylistT: TypeAlias = Type[TSongOrPlaylist]
LINK_TYPE_MAP: Dict[str, TSongOrPlaylistT] = {
    "url": Song,
    "song": Song,
    "dj": Voice,
    "program": Voice,
    "playlist": Playlist,
}
SEARCHER_COMMANDS: Dict[Type[BaseSearcher], List[str]] = {
    SongSearcher: ["点歌", "网易云", "wyy", "网易点歌", "wysong"],
    VoiceSearcher: ["网易电台", "wydj"],
    PlaylistSearcher: ["网易歌单", "wypli"],
}

_link_types_reg = "|".join(LINK_TYPE_MAP)
URL_REGEX = (
    rf"music\.163\.com/(.*?)(?P<type>{_link_types_reg})(/?\?id=|/)(?P<id>[0-9]+)&?"
)
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"


async def song_to_normal_msg(it: BaseSong) -> UniMessage:
    name, artists, cover_url = await aio.gather(
        it.get_name(),
        it.get_artists(),
        it.get_cover_url(),
    )
    content = "、".join(artists)
    return UniMessage.image(url=cover_url) + (
        f"{name}\nBy: {content}\n使用指令 `direct` 获取播放链接"
    )


async def voice_to_normal_msg(it: Voice) -> UniMessage:
    info = it.info
    return UniMessage.image(url=info.cover_url) + (
        f"{info.name}\n"
        f"电台：{info.radio.name}\n"
        f"台主：{info.dj.nickname}\n"
        f"使用指令 `direct` 获取播放链接"
    )


async def playlist_to_normal_msg(it: Playlist) -> UniMessage:
    info = it.info
    return UniMessage.image(url=info.cover_img_url) + (
        f"{info.name}\n"
        f"创建者：{info.creator.nickname}\n"
        f"{await it.get_url()}\n"
        f"使用指令 `resolve` 选择内容播放"
    )


async def to_normal_msg(it: TSongOrPlaylist) -> UniMessage:
    type_map = {
        Playlist: playlist_to_normal_msg,
        Voice: voice_to_normal_msg,
        BaseSong: song_to_normal_msg,
    }
    return await next((func(it) for t, func in type_map.items() if isinstance(it, t)))
