from nonebot import get_driver
from pydantic import BaseModel


class ConfigModel(BaseModel):
    pass


config: ConfigModel = ConfigModel.parse_obj(get_driver().config.dict())
