from typing import Annotated

from cookit.pyd import model_with_model_config
from nonebot import get_plugin_config
from nonebot.compat import PYDANTIC_V2
from pydantic import AnyHttpUrl, BaseModel, ConfigDict


def alias_generator(x: str):
    return f"ncm_{x}"


model_config: ConfigDict = {"alias_generator": alias_generator}
if PYDANTIC_V2:
    model_config["coerce_numbers_to_str"] = True


@model_with_model_config(model_config)
class ConfigModel(BaseModel):
    # login
    cookie_music_u: str | None = None
    ctcode: int = 86
    phone: str | None = None
    email: str | None = None
    password: str | None = None
    password_hash: str | None = None
    anonymous: bool = False

    # ui
    list_limit: int = 20
    list_font: str | None = None
    lrc_empty_line: str | None = "-"

    # behavior
    auto_resolve: bool = False
    resolve_cool_down: int = 30
    resolve_playable_card: bool = False
    illegal_cmd_finish: bool = False
    illegal_cmd_limit: int = 3
    delete_msg: bool = True
    delete_msg_delay: tuple[float, float] = (0.5, 2.0)
    info_contains_url: bool = True
    send_media: bool = True
    send_media_tip: bool = False
    send_media_no_unimsg_fallback: bool = True
    send_as_card: bool = True
    ignore_send_card_failure: bool = True
    send_as_file: bool = False
    ob_v11_local_mode: bool = True
    ob_v11_ignore_send_file_failure: bool = False

    # other
    msg_cache_size: int = 1024
    msg_cache_time: int = 43200
    resolve_cool_down_cache_size: int = 1024
    card_sign_url: Annotated[str, AnyHttpUrl] | None = None
    card_sign_timeout: int = 5
    ffmpeg_executable: str = "ffmpeg"
    safe_filename: bool = True
    clean_cache_on_startup: bool = True


config = get_plugin_config(ConfigModel)
