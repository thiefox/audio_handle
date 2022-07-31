import os
import re
from sys import path

YEAR_FORMAT_HEADER = r"^(\d{4})"        #专辑年份开头
YEAR_FORMAT_TAILER = r"(\d{4})$"        #专辑年份结尾
YEAR_FORMAT_MIDDLE = r"(\d{4})[ -._]"    #空格(32) -(45) .(46) _(95) []内必须按ascii序

AUDIO_FORMAT_NAMES = ('WAV', 'APE', 'MP3', 'FLAG', )
SPLITTERS = ('.', '-', ' ', )
SPLITTERS_PAIR = ( ('[', ']'), ('(', ')'), )

REMASTERED_FLAG = 'REMASTERED'

ALBUM_DIR_NAMED_MODES = ( '[year][artist][s][album]')

CHS_SORT_SUB_DIRS = ('其他', '其它', )
ENG_SORT_SUB_DIRS = ('album', 'bootleg', 'compilation', 'single', 'remaster', 'remix', 'studio', 'live', 'soundtrack', 'ep')

KEY_NAME_ARTIST_DIR = 'ARTIST_DIR'
KEY_NAME_ALBUMS = 'ALBUMS'

def sub_dirs_is_sort(path_name : str) -> bool :
    sort = False
    SORT_MATCHED_THRESHOLD = 0.8
    matched_count = 0
    subs = os.listdir(path_name)
    if len(subs) == 0 :
        return False
    for sub in subs :
        year_info = False
        info = re.search(YEAR_FORMAT_MIDDLE, sub, re.I)
        if info is not None :
            pos = info.span()
            year = info.group(1)        #取正则表达式第一对括号中内容
            if year[0] == '1' or year[0] == '2' :
                year_info = True

        if not year_info :
            if sub in CHS_SORT_SUB_DIRS or sub.lower() in ENG_SORT_SUB_DIRS :
                matched_count += 1
            else :
                for ESSD in ENG_SORT_SUB_DIRS :
                    if sub.lower().find(ESSD) >= 0 :
                        matched_count += 1
                        break

    score = float(matched_count/len(subs))
    sort = score >= SORT_MATCHED_THRESHOLD
    if sort :
        print('目录{}为分类目录。'.format(path_name))
    else :
        print('目录{}为专辑目录。'.format(path_name))

    return sort

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


def rip_info_from_dir_name(path_dir : str, artist_name : str = '', aa_dict : dict = None) -> tag_info :
    if aa_dict is not None :
        assert(artist_name != '')
    dir_name = os.path.basename(path_dir)
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
    standard_name = year + '.' + title
    print('   专辑目录标准名称(YEAR.TITLE)={}'.format(standard_name))
    if aa_dict is not None :
        assert(artist_name != '')
        assert(artist_name in aa_dict)
        artist_albums = aa_dict[artist_name]
        if KEY_NAME_ALBUMS not in artist_albums :
            albums = dict()
            albums[path_dir] = standard_name
            artist_albums[KEY_NAME_ALBUMS] = albums
        else :
            albums = artist_albums[KEY_NAME_ALBUMS]
            if path_dir in albums :
                print('异常：目录({})已经在字典中。'.format(path_dir))
                assert(False)
            assert(path_dir not in albums)
            albums[path_dir] = standard_name
            artist_albums[KEY_NAME_ALBUMS] = albums
        print('通知：目录({})加入到字典。'.format(path_dir))
    return ti

#-1=未知目录
#0=根目录，第一级子目录为艺人名
#1=艺人目录，第一级子目录为分类目录或专辑目录
#2=分类目录，第一级子目录为专辑目录
#3=专辑目录
def analysis_dir_name(path_dir : str, mode : int = -1, artist_name : str = '', aa_dict : dict = None) :
    print('目录检查：path_dir={}, mode={}, artist={}.'.format(path_dir, mode, artist_name))
    dir_name = os.path.basename(path_dir)
    if mode == -1 or mode == 3 :
        rip_info_from_dir_name(path_dir, artist_name, aa_dict)
    elif mode == 0 :
        subs = os.listdir(path_dir)
        for sub in subs :
            path_artist = os.path.join(path_dir, sub)
            analysis_dir_name(path_artist, 1, sub, aa_dict)
    elif mode == 1 :        #艺人目录
        if aa_dict is not None :
            assert(artist_name != '')
            assert(artist_name not in aa_dict)
            ai = dict()
          
            ai[KEY_NAME_ARTIST_DIR] = path_dir
            aa_dict[artist_name] = ai

        sorted = sub_dirs_is_sort(path_dir)

        subs = os.listdir(path_dir)
        for sub in subs :
            sort = False
            if sub in CHS_SORT_SUB_DIRS or sub.lower() in ENG_SORT_SUB_DIRS :
                sort = True
            else :
                for ESSD in ENG_SORT_SUB_DIRS :
                    if sub.lower() == ESSD + 's' :
                        sort = True
                        break
            
            if sort :
                path_sort = os.path.join(path_dir, sub)
                analysis_dir_name(path_sort, 2, artist_name, aa_dict)
            else :
                path_album = os.path.join(path_dir, sub)
                analysis_dir_name(path_album, 2 if sorted else 3, artist_name, aa_dict)    
    elif mode == 2 :
        sorted = sub_dirs_is_sort(path_dir)
        subs = os.listdir(path_dir)
        for sub in subs :
            path_album = os.path.join(path_dir, sub)
            analysis_dir_name(path_album, 2 if sorted else 3, artist_name, aa_dict)
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
    artist_albums = dict()
    analysis_dir_name(root, root_mode, artist_name, artist_albums)

    print('字典中共有({})个艺人信息。'.format(len(artist_albums)))
    for an in artist_albums :
        ai = artist_albums[an]
        print('艺人{}字典共有{}条key.'.format(an, len(ai)))
        for k in ai :
            print('found key={}.'.format(k))
            print(ai[k])

        ar = ai['ARTIST_DIR']
        print('艺人({})的根目录={}...'.format(an, ar))
        albums = ai['ALBUMS']
        for ap in albums :
            title = albums[ap]
            print('  专辑标准名：{}, 目录={}.'.format(title, ap))

    return

    dirs = os.listdir(root)
    for dir in dirs :
        path_dir = os.path.join(root, dir)
        rip_info_from_dir_name(path_dir, artist_name)
    return

test_rip_info_from_dir_name()