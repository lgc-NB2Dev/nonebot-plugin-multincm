from nonebot import logger, on_command
from nonebot.matcher import Matcher

from ..resolver import ResolvedSong

matcher_direct = on_command("直链", aliases={"direct"})


@matcher_direct.handle()
async def _(matcher: Matcher, song: ResolvedSong):
    try:
        url = await song.get_playable_url()
    except Exception:
        logger.exception(f"Failed to get playable url for {song}")
        await matcher.finish("获取直链失败，请检查后台输出")
    await matcher.send(url)
