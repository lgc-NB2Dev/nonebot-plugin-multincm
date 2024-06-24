from typing import cast

import anyio
from nonebot import logger
from nonebot.utils import run_sync
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

from ...config import config
from ...const import DATA_DIR

SESSION_FILE = DATA_DIR / "session.cache"


async def do_login(retry: bool = True):
    if SESSION_FILE.exists():
        logger.info(f"使用缓存登录态 ({SESSION_FILE})")
        SetCurrentSession(
            LoadSessionFromString(
                (await anyio.Path(SESSION_FILE).read_text(encoding="u8")),
            ),
        )

    elif (config.ncm_phone or config.ncm_email) and (
        config.ncm_password or config.ncm_password_hash
    ):
        retry = False

        if config.ncm_phone:
            logger.info("使用手机号登录")
            await run_sync(LoginViaCellphone)(
                ctcode=config.ncm_ctcode,
                phone=config.ncm_phone,
                password=config.ncm_password or "",
                passwordHash=config.ncm_password_hash or "",
            )

        else:
            logger.info("使用邮箱登录")
            await run_sync(LoginViaEmail)(
                email=config.ncm_email or "",
                password=config.ncm_password or "",
                passwordHash=config.ncm_password_hash or "",
            )

        await anyio.Path(SESSION_FILE).write_text(
            DumpSessionAsString(GetCurrentSession()),
            encoding="u8",
        )

    else:
        retry = False
        logger.warning("账号或密码未填写，使用游客账号登录")
        await run_sync(LoginViaAnonymousAccount)()

    try:
        ret = cast(dict, await run_sync(GetCurrentLoginStatus)())
        assert ret["code"] == 200
        assert ret["account"]
    except Exception as e:
        if await (pth := anyio.Path(SESSION_FILE)).exists():
            await pth.unlink()

        if retry:
            logger.warning("恢复缓存会话失败，尝试使用正常流程登录")
            await do_login(retry=False)
            return

        raise RuntimeError("登录态异常，请重新登录") from e

    session = GetCurrentSession()
    logger.info(f"登录成功，欢迎您，{session.nickname} [{session.uid}]")


async def login():
    # if "nonebot-plugin-ncm" in get_available_plugin_names():
    #     logger.info("nonebot-plugin-ncm 已安装，本插件将依赖其全局 Session")
    #     require("nonebot-plugin-ncm")
    #     return

    if GetCurrentSession().logged_in:
        logger.info("检测到当前全局 Session 已登录，插件将跳过登录步骤")
        return

    await do_login()
