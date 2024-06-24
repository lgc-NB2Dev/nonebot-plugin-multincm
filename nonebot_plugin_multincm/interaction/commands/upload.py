from nonebot import logger, on_command
from nonebot.matcher import Matcher

from ...config import config
from ..message import send_song_media
from ..resolver import ResolvedSong


async def upload_handler_0(matcher: Matcher, song: ResolvedSong):
    try:
        await send_song_media(song, as_file=True)
    except Exception:
        logger.exception(f"Failed to upload {song} as file")
        await matcher.finish("上传失败，请检查后台输出")


def __register_upload_matcher():
    matcher_lyric = on_command("上传", aliases={"upload"})
    matcher_lyric.handle()(upload_handler_0)


if not config.ncm_send_as_file:
    __register_upload_matcher()
