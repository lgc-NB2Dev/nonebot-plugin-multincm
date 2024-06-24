from nonebot import logger, on_command
from nonebot.matcher import Matcher
from nonebot_plugin_alconna.uniseg import UniMessage

from ...render import render_lyrics
from ..resolver import ResolvedSong

matcher_lyric = on_command("歌词", aliases={"lrc", "lyric", "lyrics"})


@matcher_lyric.handle()
async def _(matcher: Matcher, song: ResolvedSong):
    try:
        lrc = await song.get_lyrics()
    except Exception:
        logger.exception(f"Failed to get lyric for {song}")
        await matcher.finish("获取歌词失败，请检查后台输出")

    if not lrc:
        await matcher.finish("该歌曲没有歌词")

    try:
        img = await render_lyrics(groups=lrc)
    except Exception:
        logger.exception(f"Failed to render lyrics for {song}")
        await matcher.finish("渲染歌词失败，请检查后台输出")
    await UniMessage.image(raw=img).finish()
