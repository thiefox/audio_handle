import os
import re

YEAR_FORMAT_HEADER = r"^(\d{4})"        #专辑年份开头
YEAR_FORMAT_TAILER = r"(\d{4})$"        #专辑年份结尾
YEAR_FORMAT_MIDDLE = r"(\d{4})[ -._]"    #空格(32) -(45) .(46) _(95) []内必须按ascii序

AUDIO_FORMAT_NAMES = ('WAV', 'APE', 'MP3', 'FLAG', )
SPLITTERS = ('.', '-', ' ', )
SPLITTERS_PAIR = ( ('[', ']'), ('(', ')'), )

REMASTERED_FLAG = 'REMASTERED'

ALBUM_DIR_NAMED_MODES = ( '[year][artist][s][album]')

CHS_SORT_SUB_DIRS = ('其他', '其它', )
ENG_SORT_SUB_DIRS = ('album', 'bootleg', 'compilation', 'single', 'remaster', 'remix', )

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


def rip_info_from_dir_name(dir_name : str, artist_name : str = '') -> tag_info :
    ti = tag_info()
    print('专辑目录名检测={}...'.format(dir_name))
    #去除音频类型标记
    for afn in AUDIO_FORMAT_NAMES :
        dir_name = dir_name.replace(afn, '')
        dir_name = dir_name.replace(afn.lower(), '')

    year = ''
    info = re.search(YEAR_FORMAT_MIDDLE, dir_name, re.I) 
    if info is not None :
        pos = info.span()
        year = info.group(1)        #取正则表达式第一对括号中内容
        #print('   year info={}, begin={}, end={}, data={}.'.format(year, pos[0], pos[1], dir_name))
        if pos[0] == 0 :
            dir_name = dir_name[pos[1]:]    #把年份信息剔除
        else :
            dir_name = dir_name[:pos[0]-1] + dir_name[pos[1]:]    #把年份信息剔除
        #print('   after cut year info, dir_name={}.'.format(dir_name))
    else :
        #print('   not rip year info, data={}.'.format(dir_name))
        pass

    #去除中间已无数据的无效分隔符对
    for sp in SPLITTERS_PAIR :
        pos = 0
        while True :
            if pos >= len(dir_name) :
                break
            found = dir_name.find(sp[0], pos)
            if found < 0 :
                break
            elif found + 1 < len(dir_name) and dir_name[found+1] == sp[1] :
                dir_name = dir_name[:found] + dir_name[found+2:]
                pos = found + 2
            else :
                pos = found + 1

    #print('   try rip album title...')
    title = dir_name.strip()
    '''
    pos = dir_name.find(year)
    if pos >= 0 :
        title = dir_name[:pos] + dir_name[pos+len(year):]
        title = title.strip()
        print('   cut year info ok.')
    '''
    '''   #反例：花乱聚.从头认识达明一派
    if artist_name != '' :
        pos = title.find(artist_name) 
        if pos >= 0 :
            title = title[:pos] + title[pos+len(artist_name):]
            if title.strip() == '' :
                title = artist_name     #艺人同名专辑
                print('   artist same name ablum.')
    '''
    #去除头部和尾部的分隔符
    while title[0] in SPLITTERS :
        title = title[1:]
    while title[-1] in SPLITTERS :
        title = title[:-2]

    print('   专辑目录标准名称(YEAR.TITLE)={} - {}'.format(year, title))

    return ti

#-1=未知目录
#0=根目录，第一级子目录为艺人名
#1=艺人目录，第一级子目录为分类目录或专辑目录
#2=分类目录，第一级子目录为专辑目录
#3=专辑目录
def analysis_dir_name(path_dir : str, mode : int = -1, artist_name : str = '') :
    print('目录检查：path_dir={}, mode={}, artist={}.'.format(path_dir, mode, artist_name))
    dir_name = os.path.basename(path_dir)
    if mode == -1 or mode == 3 :
        rip_info_from_dir_name(dir_name, artist_name)
    elif mode == 0 :
        subs = os.listdir(path_dir)
        for sub in subs :
            path_artist = os.path.join(path_dir, sub)
            analysis_dir_name(path_artist, 1, sub)
    elif mode == 1 :
        subs = os.listdir(path_dir)
        for sub in subs :
            sort = False
            if sub in CHS_SORT_SUB_DIRS or sub.lower() in ENG_SORT_SUB_DIRS :
                sort = True
                path_sort = os.path.join(path_dir, sub)
                analysis_dir_name(path_sort, 2, artist_name)
            else :
                for ESSD in ENG_SORT_SUB_DIRS :
                    if sub.lower() == ESSD + 's' :
                        sort = True
                        break
            
            if sort :
                path_sort = os.path.join(path_dir, sub)
                analysis_dir_name(path_sort, 2, artist_name)
            else :
                path_album = os.path.join(path_dir, sub)
                analysis_dir_name(path_album, 3, artist_name)    
    elif mode == 2 :
        subs = os.listdir(path_dir)
        for sub in subs :
            path_album = os.path.join(path_dir, sub)
            analysis_dir_name(path_album, 3, artist_name)
    else :
        print('参数异常：path_dir={}, mode={}, artist={}.'.format(path_dir, mode, artist_name))
    return

def test_rip_info_from_dir_name() :
    root = 'Y:\\MUSES\\华语乐队\\达明一派'
    #root = 'Y:\\MUSES\\华语女艺人\\蔡健雅'
    #root = 'Y:\\MUSES\\欧美乐队\\Black Box Recorder'
    root = 'Y:\\MUSES\\欧美男艺人\\David Bowie'
    root_mode = 1
    artist_name = 'David Bowie'
    analysis_dir_name(root, root_mode, artist_name)
    return

    dirs = os.listdir(root)
    for dir in dirs :
        rip_info_from_dir_name(dir, artist_name)
    return

test_rip_info_from_dir_name()