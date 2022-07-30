import os

YEAR_FORMAT = r"(\d{4})"       #专辑年份
AUDIO_FORMAT_NAMES = ('WAV', 'APE', 'MP3', 'FLAG', )
SPLITTERS = ('.', '-', ' ', )
SPLITTERS_PAIR = ( ('[', ']'), ('(', ')'), )

REMASTERED_FLAG = 'REMASTERED'

class tag_info :
    def __init__(self) -> None:
        self.artist_name = ''       #歌曲表演艺人，有多个艺人则用|分隔
        self.album_artist = ''      #专辑表演艺人，有多个艺人则用|分隔
        self.album_name = ''
        self.year = 1970            #专辑发布年份
        self.CD_serial = 0          #用于多CD专辑
        self.track = 0              #音频轨道号
        self.track_count = 0        #音轨所属CD的总音轨数量
        self.title = ''             #歌曲名称
        self.genre = ''             #专辑流派
        self.comment = ''           #注释
        return


def rip_info_from_dir_name(path_name : str, artist_name : str = '') -> tag_info :
    ti = tag_info()

    return ti