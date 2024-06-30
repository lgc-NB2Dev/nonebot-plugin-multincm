from httpx import AsyncClient
from nonebot_plugin_alconna.builtins.uniseg.music_share import (
    MusicShare,
    MusicShareKind,
)
from nonebot_plugin_alconna.uniseg import UniMessage

from ...config import config
from ...data_source import BaseSong


async def sign_music_card(song: BaseSong) -> str:
    assert config.ncm_card_sign_url
    info = await song.get_info()
    async with AsyncClient(
        follow_redirects=True,
        timeout=config.ncm_card_sign_timeout,
    ) as cli:
        body = {
            "type": "custom",
            "url": info.url,
            "audio": info.playable_url,
            "title": info.display_name,
            "image": info.cover_url,
            "singer": info.display_artists,
        }
        return (
            (await cli.post(config.ncm_card_sign_url, json=body))
            .raise_for_status()
            .text
        )


async def send_song_card_msg(song: BaseSong):
    if config.ncm_card_sign_url:
        return await UniMessage.hyper("json", await sign_music_card(song)).send()
    info = await song.get_info()
    return await UniMessage(
        MusicShare(
            kind=MusicShareKind.NeteaseCloudMusic,
            title=info.display_name,
            content=info.display_artists,
            url=info.url,
            thumbnail=info.cover_url,
            audio=info.playable_url,
            brief=info.display_artists,
        ),
    ).send()
