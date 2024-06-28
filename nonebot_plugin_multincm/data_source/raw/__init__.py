from . import models
from .login import login as login
from .request import (
    get_album_info as get_album_info,
    get_playlist_info as get_playlist_info,
    get_program_info as get_program_info,
    get_radio_info as get_radio_info,
    get_radio_programs as get_radio_programs,
    get_search_result as get_search_result,
    get_track_audio as get_track_audio,
    get_track_info as get_track_info,
    get_track_lrc as get_track_lrc,
    ncm_request as ncm_request,
    search_album as search_album,
    search_playlist as search_playlist,
    search_program as search_program,
    search_radio as search_radio,
    search_song as search_song,
)

md = models
del models
