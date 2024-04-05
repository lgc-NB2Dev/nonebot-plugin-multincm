import json
from typing import TypedDict

from .const import RES_DIR

MUSIC_CARD_TEMPLATE_PATH = RES_DIR / "card_template.json"


class CardConfigDict(TypedDict):
    ctime: int
    forward: int
    token: str
    type: str


class CardExtraDict(TypedDict):
    app_type: int
    appid: int
    # msg_seq: int
    uin: int


class CardMetaMusicDict(TypedDict):
    action: str
    android_pkg_name: str
    app_type: int
    appid: int
    ctime: int
    desc: str
    jumpUrl: str
    musicUrl: str
    preview: str
    sourceMsgId: str
    source_icon: str
    source_url: str
    tag: str
    title: str
    uin: int


class CardMetaDict(TypedDict):
    music: CardMetaMusicDict


class CardDict(TypedDict):
    app: str
    config: CardConfigDict
    extra: CardExtraDict
    meta: CardMetaDict
    prompt: str
    ver: str
    view: str


MUSIC_CARD_TEMPLATE: CardDict = json.loads(MUSIC_CARD_TEMPLATE_PATH.read_text("u8"))


async def sign_card(card_json: str) -> str:
    # placeholder
    return card_json


async def construct_music_card(
    *,
    uin: int,
    desc: str,
    jump_url: str,
    music_url: str,
    preview: str,
    title: str,
    sign: bool = True,
) -> str:
    data = MUSIC_CARD_TEMPLATE.copy()
    # ctime = int(time.time())
    # config = data["config"]
    extra = data["extra"]
    meta = data["meta"]["music"]
    # config["ctime"] = ctime
    extra["uin"] = uin
    # meta["ctime"] = ctime
    meta["desc"] = desc
    meta["jumpUrl"] = jump_url
    meta["musicUrl"] = music_url
    meta["preview"] = preview
    meta["title"] = title
    meta["uin"] = uin
    data["prompt"] = f"[分享]{title}"
    card_json = json.dumps(data)
    return await sign_card(card_json) if sign else card_json
