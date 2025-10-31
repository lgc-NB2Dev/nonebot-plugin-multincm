from cookit.loguru import warning_suppress
from cookit.nonebot.alconna import RecallContext
from nonebot_plugin_alconna.uniseg import UniMessage

from ...config import config
from ...data_source import BasePlaylist, BaseSong
from ...utils import is_song_card_supported
from ..cache import set_cache
from .song_card import send_song_card_msg
from .song_file import send_song_media

SONG_TIP = "\n使用指令 `direct` 获取播放链接"
PLAYLIST_TIP = "\n使用指令 `resolve` 选择内容播放"


async def construct_info_msg(
    it: BaseSong | BasePlaylist,
    tip_command: bool = True,
) -> UniMessage:
    tip = (
        next(
            v
            for k, v in {BaseSong: SONG_TIP, BasePlaylist: PLAYLIST_TIP}.items()
            if isinstance(it, k)
        )
        if tip_command
        else ""
    )
    info = await it.get_info()
    desc = await info.get_description()
    msg = UniMessage.image(url=info.cover_url) + desc
    if config.info_contains_url:
        msg += f"\n{info.url}"
    msg += f"\n{tip}"
    return msg


async def _send_song_without_cache(song: BaseSong):
    if config.send_as_card and is_song_card_supported():
        with warning_suppress(f"Send {song} card failed"):
            await send_song_card_msg(song)
            return
        if config.ignore_send_card_failure:
            return

    if not config.send_media:
        await (await construct_info_msg(song, tip_command=True)).send()

    else:
        receipt = None
        async with RecallContext() as recall:
            await recall.send(UniMessage.text("处理中，请稍等哦~"))
            with warning_suppress(f"Send {song} file failed"):
                receipt = await send_song_media(song)

        await (await construct_info_msg(song, tip_command=False)).send(
            reply_to=(
                (r[0] if (r := receipt.get_reply()) else None) if receipt else None
            ),
        )


async def send_song(song: BaseSong):
    await _send_song_without_cache(song)
    await set_cache(song)
