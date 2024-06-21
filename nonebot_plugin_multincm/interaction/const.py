from typing import Dict, List, Type

from ..data_source import (
    BaseSearcher,
    PlaylistSearcher,
    SongSearcher,
    VoiceSearcher,
    registered_resolvable,
)

SEARCHER_COMMANDS: Dict[Type[BaseSearcher], List[str]] = {
    SongSearcher: ["点歌", "网易云", "wyy", "网易点歌", "wydg", "wysong"],
    VoiceSearcher: ["网易电台", "wydt", "wydj"],
    PlaylistSearcher: ["网易歌单", "wygd", "wypli"],
}
EXIT_COMMAND = (
    "退出", "tc", "取消", "qx", "quit", "q", "exit", "e", "cancel", "c", "0",
)  # fmt: skip
PREVIOUS_COMMAND = ("上一页", "syy", "previous", "p")
NEXT_COMMAND = ("下一页", "xyy", "next", "n")
JUMP_PAGE_PREFIX = ("page", "p", "跳页", "页")

_link_types_reg = "|".join(registered_resolvable)
URL_REGEX = (
    rf"music\.163\.com/(.*?)(?P<type>{_link_types_reg})(/?\?id=|/)(?P<id>[0-9]+)&?"
)
SHORT_URL_BASE = "https://163cn.tv"
SHORT_URL_REGEX = r"163cn\.tv/(?P<suffix>[a-zA-Z0-9]+)"
