from pathlib import Path
from typing import Annotated, Optional, Tuple
from urllib.parse import quote

from nonebot import get_plugin_config
from pydantic import AnyHttpUrl, BaseModel


class ConfigModel(BaseModel):
    # login
    ncm_ctcode: int = 86
    ncm_phone: Optional[str] = None
    ncm_email: Optional[str] = None
    ncm_password: Optional[str] = None
    ncm_password_hash: Optional[str] = None

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
    ncm_delete_msg_delay: Tuple[float, float] = (0.5, 2.0)
    ncm_send_as_card: bool = True
    ncm_send_as_file: bool = False

    # other
    ncm_msg_cache_size: int = 1024
    ncm_msg_cache_time: int = 43200
    ncm_resolve_cool_down_cache_size: int = 1024
    ncm_card_sign_url: Optional[Annotated[str, AnyHttpUrl]] = None
    ncm_card_sign_timeout: int = 5
    ncm_ob_v11_local_mode: bool = False

    @property
    def ncm_list_font_url(self) -> Optional[str]:
        return (
            quote(p.as_uri())
            if self.ncm_list_font and (p := Path(self.ncm_list_font)).exists()
            else self.ncm_list_font
        )


config = get_plugin_config(ConfigModel)
