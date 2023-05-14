import asyncio
from pathlib import Path
from typing import cast

import anyio
from nonebot import get_available_plugin_names, logger, require
from pyncm import (
    DumpSessionAsString,
    GetCurrentSession,
    LoadSessionFromString,
    SetCurrentSession,
)
from pyncm.apis.login import (
    GetCurrentLoginStatus,
    LoginViaAnonymousAccount,
    LoginViaCellphone,
    LoginViaEmail,
)

from .config import config
from .utils import awaitable

DATA_PATH = Path().cwd() / "data" / "multincm"
if not DATA_PATH.exists():
    DATA_PATH.mkdir(parents=True)

SESSION_FILE = DATA_PATH / "session.cache"


async def login():
    if SESSION_FILE.exists():
        logger.info(f"使用缓存登录态 ({str(SESSION_FILE)})")
        SetCurrentSession(
            LoadSessionFromString(
                (await anyio.Path(SESSION_FILE).read_text(encoding="u8")),
            ),
        )

    elif (config.ncm_phone or config.ncm_email) and (
        config.ncm_password or config.ncm_password_hash
    ):
        if config.ncm_phone:
            logger.info("使用手机号登录")
            await awaitable(LoginViaCellphone)(
                ctcode=config.ncm_ctcode,
                phone=config.ncm_phone,
                password=config.ncm_password or "",
                passwordHash=config.ncm_password_hash or "",
            )

        else:
            logger.info("使用邮箱登录")
            await awaitable(LoginViaEmail)(
                email=config.ncm_email or "",
                password=config.ncm_password or "",
                passwordHash=config.ncm_password_hash or "",
            )

        await anyio.Path(SESSION_FILE).write_text(
            DumpSessionAsString(GetCurrentSession()),
            encoding="u8",
        )

    else:
        logger.warning("账号或密码未填写，使用游客账号登录")
        await awaitable(LoginViaAnonymousAccount)()

    try:
        ret = cast(dict, await awaitable(GetCurrentLoginStatus)())
        assert ret["code"] == 200
        assert ret["account"]
    except Exception as e:
        if await (pth := anyio.Path(SESSION_FILE)).exists():
            await pth.unlink()
        raise RuntimeError("检查登录态异常，已删除缓存登录态，请重新登录") from e

    session = GetCurrentSession()
    logger.info(f"登录成功，欢迎您，{session.nickname} [{session.uid}]")


if "nonebot-plugin-ncm" in get_available_plugin_names():
    logger.info("nonebot-plugin-ncm 已安装，本插件将依赖其全局 Session")
    require("nonebot-plugin-ncm")
else:
    asyncio.get_event_loop().run_until_complete(login())
