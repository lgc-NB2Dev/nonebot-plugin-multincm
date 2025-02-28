from typing import Annotated, Optional

from cookit.pyd import get_model_with_config
from nonebot import get_plugin_config
from nonebot.compat import PYDANTIC_V2
from pydantic import AnyHttpUrl, BaseModel

BaseConfigModel = (
    get_model_with_config({"coerce_numbers_to_str": True}) if PYDANTIC_V2 else BaseModel
)


class ConfigModel(BaseConfigModel):
    # login
    ncm_ctcode: int = 86
    ncm_phone: Optional[str] = None
    ncm_email: Optional[str] = None
    ncm_password: Optional[str] = None
    ncm_password_hash: Optional[str] = None
    ncm_anonymous: bool = False

    # ui
    ncm_list_limit: int = 20
    ncm_list_font: Optional[str] = None
    ncm_lrc_empty_line: Optional[str] = "-"

    # behavior
    ncm_auto_resolve: bool = False
    ncm_resolve_cool_down: int = 30
    ncm_resolve_playable_card: bool = False
    ncm_illegal_cmd_finish: bool = False
    ncm_illegal_cmd_limit: int = 3
    ncm_delete_msg: bool = True
    ncm_delete_msg_delay: tuple[float, float] = (0.5, 2.0)
    ncm_send_media: bool = True
    ncm_send_as_card: bool = True
    ncm_send_as_file: bool = False

    # other
    ncm_msg_cache_size: int = 1024
    ncm_msg_cache_time: int = 43200
    ncm_resolve_cool_down_cache_size: int = 1024
    ncm_card_sign_url: Optional[Annotated[str, AnyHttpUrl]] = None
    ncm_card_sign_timeout: int = 5
    ncm_ob_v11_local_mode: bool = False
    ncm_ffmpeg_executable: str = "ffmpeg"


config = get_plugin_config(ConfigModel)
