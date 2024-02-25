from typing import Optional, Tuple

from nonebot import get_driver
from pydantic import BaseModel, validator


class ConfigModel(BaseModel):
    ncm_ctcode: int = 86
    ncm_phone: Optional[str] = None
    ncm_email: Optional[str] = None
    ncm_password: Optional[str] = None
    ncm_password_hash: Optional[str] = None

    ncm_list_limit: int = 20
    ncm_list_font: Optional[str] = None
    ncm_max_name_len: int = 600
    ncm_max_artist_len: int = 400
    ncm_use_playwright: bool = False
    ncm_lrc_empty_line: Optional[str] = "--------"

    ncm_msg_cache_time: int = 43200
    ncm_auto_resolve: bool = False
    ncm_resolve_playable_card: bool = False
    ncm_illegal_cmd_finish: bool = False
    ncm_illegal_cmd_limit: int = 3
    ncm_delete_list_msg: bool = True
    ncm_delete_list_msg_delay: Tuple[float, float] = (0.5, 2.0)
    ncm_upload_folder_name: str = "MultiNCM"
    ncm_enable_record: bool = False

    @validator("ncm_upload_folder_name")
    def validate_upload_folder_name(cls, v: str) -> str:  # noqa: N805
        v = v.strip("/")
        if "/" in v:
            raise ValueError("Upload folder name cannot contain `/`")
        return v


config: ConfigModel = ConfigModel.parse_obj(get_driver().config.dict())
