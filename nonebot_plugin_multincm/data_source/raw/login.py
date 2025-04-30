import asyncio
import time
from pathlib import Path
from typing import Any, Optional

import anyio
import qrcode
from cookit.loguru import warning_suppress
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
    LoginFailedException,
    LoginQrcodeCheck,
    LoginQrcodeUnikey,
    LoginViaAnonymousAccount,
    LoginViaCellphone,
    LoginViaEmail,
    SetSendRegisterVerifcationCodeViaCellphone,
    WriteLoginInfo,
)

from ...config import config
from ...const import SESSION_FILE_PATH
from .request import NCMResponseError, ncm_request


async def sms_login(phone: str, country_code: int = 86):
    timeout = 60

    while True:
        await ncm_request(
            SetSendRegisterVerifcationCodeViaCellphone,
            phone,
            country_code,
        )
        last_send_time = time.time()
        logger.success(
            f"已发送验证码到 +{country_code} {'*' * (len(phone) - 3)}{phone[-3:]}",
        )

        while True:
            captcha = input("> 请输入验证码，留空直接回车代表重发: ").strip()
            if not captcha:
                if (time_passed := (time.time() - last_send_time)) >= timeout:
                    break
                logger.warning(f"请等待 {timeout - time_passed:.0f} 秒后再重发")
                continue

            try:
                await ncm_request(
                    LoginViaCellphone,
                    phone=phone,
                    ctcode=country_code,
                    captcha=captcha,
                )
            except LoginFailedException as e:
                data: dict[str, Any] = e.args[0]
                if data.get("code") != 503:
                    raise
                logger.error("验证码错误，请重新输入")
            else:
                return


async def phone_login(
    phone: str,
    password: str = "",
    password_hash: str = "",
    country_code: int = 86,
):
    await run_sync(LoginViaCellphone)(
        ctcode=country_code,
        phone=phone,
        password=password,
        passwordHash=password_hash,
    )


async def email_login(
    email: str,
    password: str = "",
    password_hash: str = "",
):
    await run_sync(LoginViaEmail)(
        email=email,
        password=password,
        passwordHash=password_hash,
    )


async def qrcode_login():
    async def wait_scan(uni_key: str) -> bool:
        last_status: Optional[int] = None
        while True:
            await asyncio.sleep(2)
            try:
                await ncm_request(LoginQrcodeCheck, uni_key)
            except NCMResponseError as e:
                code = e.code
                if code != last_status:
                    last_status = code
                    extra_tip = (
                        f" (用户：{e.data.get('nickname')})" if code == 802 else ""
                    )
                    logger.info(f"当前二维码状态：[{code}] {e.message}{extra_tip}")
                if code == 800:
                    return False  # 二维码过期
                if code == 803:
                    return True  # 授权成功
                if code and (code >= 1000):
                    raise

    while True:
        uni_key: str = (await ncm_request(LoginQrcodeUnikey))["unikey"]

        url = f"https://music.163.com/login?codekey={uni_key}"
        qr = qrcode.QRCode()
        qr.add_data(url)

        logger.info("请使用网易云音乐 APP 扫描下方二维码完成登录")
        qr.print_ascii()

        qr_img_filename = "multincm-qrcode.png"
        qr_img_path = Path.cwd() / qr_img_filename
        with warning_suppress("Failed to save qrcode image"):
            qr.make_image().save(
                str(qr_img_path),  # type: ignore
            )
            logger.info(
                f"二维码图片已保存至 Bot 根目录的 {qr_img_filename} 文件"
                f"，如终端中二维码无法扫描可使用",
            )

        logger.info("或使用下方 URL 生成二维码扫描登录：")
        logger.info(url)

        try:
            scan_res = await wait_scan(uni_key)
        finally:
            with warning_suppress("Failed to delete qrcode image"):
                qr_img_path.unlink(missing_ok=True)
        if scan_res:
            return


async def anonymous_login():
    await ncm_request(LoginViaAnonymousAccount)


async def validate_login():
    with warning_suppress("Failed to get login status"):
        ret = await ncm_request(GetCurrentLoginStatus)
        ok = bool(ret.get("account"))
        if ok:
            WriteLoginInfo(ret, GetCurrentSession())
        return ok
    return False


async def do_login(anonymous: bool = False):
    using_cached_session = False

    if anonymous:
        logger.info("使用游客身份登录")
        await anonymous_login()

    elif using_cached_session := SESSION_FILE_PATH.exists():
        logger.info(f"使用缓存登录态 ({SESSION_FILE_PATH})")
        SetCurrentSession(
            LoadSessionFromString(
                (await anyio.Path(SESSION_FILE_PATH).read_text(encoding="u8")),
            ),
        )

    elif config.ncm_phone:
        if config.ncm_password or config.ncm_password_hash:
            logger.info("使用手机号与密码登录")
            await phone_login(
                config.ncm_phone,
                config.ncm_password or "",
                config.ncm_password_hash or "",
            )
        else:
            logger.info("使用短信验证登录")
            await sms_login(config.ncm_phone)

    elif (has_password := bool(config.ncm_password or config.ncm_password_hash)) and (
        config.ncm_email
    ):
        logger.info("使用邮箱与密码登录")
        await email_login(
            config.ncm_email,
            config.ncm_password or "",
            config.ncm_password_hash or "",
        )

    else:
        if not has_password:
            logger.warning("配置文件中提供了邮箱，但是通过邮箱登录需要提供密码")
        logger.info("使用二维码登录")
        await qrcode_login()

    if not (await validate_login()) and using_cached_session:
        SESSION_FILE_PATH.unlink()
        logger.warning("恢复缓存会话失败，尝试使用正常流程登录")
        await do_login()
        return

    session_exists = GetCurrentSession()
    if anonymous:
        logger.success("游客登录成功")
    else:
        if not using_cached_session:
            SESSION_FILE_PATH.write_text(
                DumpSessionAsString(session_exists),
                "u8",
            )
        logger.success(
            f"登录成功，欢迎您，{session_exists.nickname} [{session_exists.uid}]",
        )


async def login():
    # if "nonebot-plugin-ncm" in get_available_plugin_names():
    #     logger.info("nonebot-plugin-ncm 已安装，本插件将依赖其全局 Session")
    #     require("nonebot-plugin-ncm")
    #     return

    if GetCurrentSession().logged_in:
        logger.info("检测到当前全局 Session 已登录，插件将跳过登录步骤")
        return

    if not config.ncm_anonymous:
        with warning_suppress("登录失败，回落到游客登录"):
            await do_login()
            return

    with warning_suppress("登录失败"):
        await do_login(anonymous=True)
