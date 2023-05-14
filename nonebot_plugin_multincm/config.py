from typing import Optional

from nonebot import get_driver
from pydantic import BaseModel


class ConfigModel(BaseModel):
    ncm_ctcode: int = 86
    ncm_phone: Optional[str] = None
    ncm_email: Optional[str] = None
    ncm_password: Optional[str] = None
    ncm_password_hash: Optional[str] = None
    ncm_list_limit: int = 20
    ncm_list_font: Optional[str] = None


config: ConfigModel = ConfigModel.parse_obj(get_driver().config.dict())
