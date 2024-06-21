from . import models
from .login import login as login
from .request import (
    get_playlist_info as get_playlist_info,
    get_search_result as get_search_result,
    get_track_audio as get_track_audio,
    get_track_info as get_track_info,
    get_track_lrc as get_track_lrc,
    get_voice_info as get_voice_info,
    ncm_request as ncm_request,
    search_playlist as search_playlist,
    search_song as search_song,
    search_voice as search_voice,
)

md = models
del models
