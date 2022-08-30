from genericpath import isdir, isfile
import os
import sys
import re
import json
from sre_parse import SPECIAL_CHARS
from sys import path
from datetime import datetime 

import langconv

import StrHandler

YEAR_FORMAT_HEADER = r"^(\d{4})"        #专辑年份开头
YEAR_FORMAT_TAILER = r"(\d{4})$"        #专辑年份结尾
YEAR_FORMAT_MIDDLE = r"(\d{4})[ -._]"    #空格(32) -(45) .(46) _(95) []内必须按ascii序

AUDIO_FORMAT_NAMES = ('WAV', 'APE', 'MP3', 'FLAC', 'AAC', 'M4A', )
SPLITTERS = ('.', '-', '_', ' ', )
SPLITTERS_PAIR = ( ('[', ']'), ('(', ')'), )

REMASTERED_FLAG = 'REMASTERED'

ALBUM_DIR_NAMED_MODES = ( '[year][artist][s][album]')

CHS_SORT_SUB_DIRS = ('其他', '其它', )
ENG_SORT_SUB_DIRS = ('album', 'bootleg', 'compilation', 'single', 'remaster', 'remix', 'studio', 'live', 'soundtrack', 'ep', )
ALBUM_SORT_NAMES = ('SINGLE', 'EP', )
INFO_SUFFIXS = ('', 'EDIT', )

SPECIAL_WORDS = ('VA', '群星', )
SPECIAL_WORDS_SUFFIX = ' -'

#ALBUM_NAME_SPLITTERS = r'[-()\[\]]'
ENG_ALBUM_NAME_SPLITTERS_MATCH = r'(-|_|\.|\(|\)|\[|\])\s*'       # 分隔符："-_()[]"，后面带N个空格
ALBUM_NAME_SPLITTERS = ('-', '.', '_', '(', ')', '[', ']', '《', '》', '+', )

CHS_ALBUM_NAME_SPLITTERS_MATCH = r'(-|_| |《|》|\+|\.|\(|\)|\[|\])\s*'

SPLITTER_SPACE = ' '

KEY_NAME_ARTIST_DIR = 'ARTIST_DIR'
KEY_NAME_ALBUMS = 'ALBUMS'

IGNORE_WORDS = ('320K', '分轨', '专辑', 'WAV整轨', 'FLAC分轨', '原抓', 'APE整轨', 'APE分轨', 'LPCD', 'AMCD', )
IGNORE_DIRS = ('ARTWORK', 'ART', 'COVERS', 'COVER', 'SCANS', )

# 转换繁体到简体
def cht_to_chs(str) :
    line = langconv.Converter('zh-hans').convert(str)
    line.encode('utf-8')
    return line

def get_data_path() -> str :
    cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    data_dir = os.path.join(cur_path, 'data')
    if not os.path.isdir(data_dir) :
        try :
            os.mkdir(data_dir)
        except Exception as e :
             err_info = "创建data目录(%s)失败，原因：%s." %(data_dir, str(e))
             print(err_info)
             data_dir = ''
    return data_dir

def get_log_path() -> str :
    cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    log_dir = os.path.join(cur_path, 'log')
    if not os.path.isdir(log_dir) :
        try :
            os.mkdir(log_dir)
        except Exception as e :
             err_info = "创建log目录(%s)失败，原因：%s." %(log_dir, str(e))
             print(err_info)
             log_dir = ''
    return log_dir    

def export_json(root_name : str, info_dict : dict) :
    str_now = datetime.strftime(datetime.now(), '%Y-%m-%d %H-%M-%S')
    file_name = 'dir_renames_({})_{}.json'.format(root_name, str_now)
    path_dir = get_data_path()
    if path_dir != '' :
        path_file = os.path.join(path_dir, file_name)
        with open(path_file, 'w', encoding='utf-8') as f:
            json.dump(info_dict, f, ensure_ascii=False, indent=1)
    return

def import_json(path_file : str) -> dict :
    info_dict = dict()
    with open(path_file, encoding='utf-8') as f:
        info_dict = json.load(f)
    return info_dict

def is_year_info(info : str) -> bool :
    year = False
    if len(info) == 4 and info.isdigit() :
        yi = int(info)
        year = yi >= 1900 and yi <= 3000
    return year

def is_matched_band_name(band_name : str, info : str) -> bool :
    if band_name == '' or info == '' :
        return False
    if band_name.upper() == info.upper() :
        return True
    if band_name.endswith('乐队') and band_name[:-2].upper() == info.upper() :
        return True
    if info.endswith('乐队') and info[:-2].upper() == band_name.upper() :
        return True
    return False

#检测一个目录下是否有音频文件(不检查子目录)
def is_audio_dir(path_dir) -> bool :
    audio = False
    items = os.listdir(path_dir)
    all_files = audio_files = 0
    for item in items :
        path_item = os.path.join(path_dir, item)
        if os.path.isfile(path_item) :
            all_files += 1
            suffix = os.path.splitext(item)[1][1:]     #不要分隔符
            if suffix.upper() in AUDIO_FORMAT_NAMES :
                audio_files += 1
    print('目录{}下共有{}个文件，其中音频{}个。'.format(path_dir, all_files, audio_files))
    audio = audio_files > 0
    return audio

#一级子目录名里含有固定单词的比例
def sub_dirs_has_text(path_name : str, word : str) -> float :
    score = float(0.0)
    found = 0
    subs = os.listdir(path_name)
    if len(subs) == 0 :
        return score
    for sub in subs :
        if sub.upper().find(word.upper()) >= 0 :
            found += 1
    score = found / len(subs)
    return score

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
        print('目录{}的子目录为分类目录。'.format(path_name))
    else :
        print('目录{}的子目录为专辑目录。'.format(path_name))

    return sort

class tag_info :
    def __init__(self) -> None:
        self.title = ''             #歌曲名称
        self.artist_name = ''       #歌曲表演艺人，有多个艺人则用|分隔
        self.album_artist = ''      #专辑表演艺人，有多个艺人则用|分隔
        self.album_name = ''        #专辑名称
        self.track = 0              #音频轨道号
        self.year = ''              #专辑发布时间（字符串格式，支持4位年份或者6位年份月份）
        self.genre = ''             #专辑流派
        self.disc_serial = 1        #用于多CD专辑(单CD专辑为1，双CD专辑为1/2)
        self.track_count = 0        #音轨所属disc的总音轨数量
        self.comment = ''           #注释
        return

    def get_play_artist(self) -> str :
        return self.artist_name if self.artist_name != '' else self.album_artist

    def get_album_artist(self) -> str :
        return self.album_artist if self.album_artist != '' else self.artist_name

    def is_same_artist(self) -> bool :
        samed = False
        if (self.album_artist == '' and self.artist_name != '') or (self.album_artist != '' and self.artist_name == '' ) :
            samed = True
        elif self.album_artist.lower() == self.artist_name.lower() :
            samed = True
        return samed
    #返回4位数的发布年份信息
    def get_release_year_str(self) -> str :
        year = ''
        if len(self.year) >= 4 :
            if len(self.year) == 4 :
                year = self.year
            else :
                year = self.year[:4]
            assert(year.isdigit())
        return year
    #返回发布时间信息，可能4位（2004），可能6位（200405）
    def get_release_date_str(self) -> str :
        date = ''
        if len(self.year) >= 4 :
            date = self.year
            assert(date.isdigit())
        return date

#如ignore_artist为TRUE，则目录名中如果有艺人名，剔除该艺人名。
def rip_info_from_dir_name(path_dir : str, artist_name : str = '', aa_dict : dict = None, ignore_artist :bool = False) -> tag_info :
    PRINT_DETAIL = False

    if aa_dict is not None :
        assert(artist_name != '')
    artist_name = cht_to_chs(artist_name)
    dir_name = os.path.basename(path_dir)
    if dir_name == '五条人《故事会》 2018 WAV' :
        PRINT_DETAIL = True
    
    is_chs = StrHandler.is_lang_zh(dir_name, Percent=0.1)
    

    ti = tag_info()
    print('专辑目录名检测={}, artist_name={}, IA={}。中文名专辑={}.'.format(dir_name, artist_name, ignore_artist, is_chs))

    SORT_LIST = list()
    for sn in ALBUM_SORT_NAMES :
        for su in INFO_SUFFIXS :
            check_name = (sn + ' ' + su).strip()
            SORT_LIST.append(check_name)

    link_name = ''
    ignored = False
    year = ''
    sort = ''       #EP OR SINGLE之类
    last_spliter = ''
    infos = None
    if is_chs : 
        infos = re.split(CHS_ALBUM_NAME_SPLITTERS_MATCH, dir_name)
    else :
        infos = re.split(ENG_ALBUM_NAME_SPLITTERS_MATCH, dir_name)

    if infos[0] == dir_name :
        print('模式匹配串分割失败，尝试空格分割...')
        infos = dir_name.split(SPLITTER_SPACE)

    for info in infos :
        if info is None :
            continue
        info = info.strip()
        info = cht_to_chs(info)
        if info.strip() == '' :
            continue
        if PRINT_DETAIL :
            print('片段({})处理...'.format(info))
        if is_matched_band_name(artist_name, info) and ignore_artist and not ignored :      #忽略艺人名处理
            ignored = True
            if PRINT_DETAIL :
                print('片段({})为艺人名，忽略。'.format(info))
            continue

        if info in ALBUM_NAME_SPLITTERS :   #分隔符
            last_spliter = info
            continue
        if info.upper() in IGNORE_WORDS : #忽略词
            if PRINT_DETAIL :
                print('片段({})为忽略单词。'.format(info))
            continue
        if info.upper() in AUDIO_FORMAT_NAMES :     #音频类型标记
            if PRINT_DETAIL :
                print('片段({})为音频类型标记。'.format(info))
            continue        #忽略
        if is_year_info(info) and year == '' :
            year = info
            if PRINT_DETAIL :
                print('片段({})为年份信息。'.format(info))
            continue
        if info.upper() in SORT_LIST and sort == '' :   #分类标记（EP/SINGLE）
            sort = info.upper().split(' ', 1)[0]
            if PRINT_DETAIL :
                print('片段({})为作品分类标记。'.format(info))
            continue
        if info.upper() in SPECIAL_WORDS :              #特殊词，VA/群星之类
            print('找到特殊词={}.'.format(info))
            if len(link_name) > 0 and link_name[-1] != ' ' :
                link_name += ' '
            link_name = link_name + info.upper() + SPECIAL_WORDS_SUFFIX
            continue

        if PRINT_DETAIL :
            print('片段({})为普通文本，做专辑名处理。last_spliter=({})。'.format(info, last_spliter))
        if last_spliter == '' :
            link_name += info
        else :
            if last_spliter == '(' or last_spliter == '[' :
                link_name += '(' + info + ')'
            elif last_spliter == '-' or last_spliter == '.' :
                if len(link_name) > 0 and link_name[-1] != ' ' :
                    link_name += ' '
                link_name = link_name + info
            else :
                if len(link_name) > 0 and link_name[-1] != ' ' :
                    link_name += ' '
                link_name = link_name + info

    if year != '' :
        link_name = year + '. ' + link_name
    if sort != '' :
        link_name = link_name + ' [' + sort + ']'

    '''
    #去除音频类型标记
    for afn in AUDIO_FORMAT_NAMES :
        dir_name = dir_name.replace(afn, '')
        dir_name = dir_name.replace(afn.lower(), '')

    #萃取年份
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

    #去除分类标记ep single

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

    '''
    pos = dir_name.find(year)
    if pos >= 0 :
        title = dir_name[:pos] + dir_name[pos+len(year):]
        title = title.strip()
        print('   cut year info ok.')
    '''
    '''   #反例：天花乱聚.从头认识达明一派
    if artist_name != '' :
        pos = title.find(artist_name) 
        if pos >= 0 :
            title = title[:pos] + title[pos+len(artist_name):]
            if title.strip() == '' :
                title = artist_name     #艺人同名专辑
                print('   artist same name ablum.')
    '''

    '''
    #去除头部和尾部的分隔符
    while title[0] in SPLITTERS :
        title = title[1:]
    while title[-1] in SPLITTERS :
        title = title[:-2]
    standard_name = ''
    if year.strip() == '' :
        standard_name = title.strip()
    else :
        standard_name = year.strip() + '. ' + title.strip()
    print('   专辑目录标准名称(YEAR.TITLE)={}'.format(standard_name))
    '''

    standard_name = link_name

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
        print('通知：目录={}加入到字典，标准名={}。'.format(path_dir, standard_name))
    return ti

#-1=未知目录
#0=根目录，第一级子目录为艺人名
#1=艺人目录，第一级子目录为分类目录或专辑目录
#2=分类目录，第一级子目录为专辑目录
#3=专辑目录
def analysis_dir_name(path_dir : str, mode : int = -1, artist_name : str = '', aa_dict : dict = None, ignore_artist : bool = False) :
    print('目录检查：path_dir={}, mode={}, artist={}.'.format(path_dir, mode, artist_name))
    dir_name = os.path.basename(path_dir)
    if mode == -1 or mode == 3 :    #专辑目录或未知目录
        #先处理子目录
        subs = os.listdir(path_dir)
        for sub in subs :
            path_sub = os.path.join(path_dir, sub)
            if os.path.isdir(path_sub) :
                analysis_dir_name(path_sub, mode, artist_name, aa_dict, ignore_artist)
        #后处理自身
        #if is_audio_dir(path_dir) :
        rip_info_from_dir_name(path_dir, artist_name, aa_dict, ignore_artist)
    elif mode == 0 :                #根目录，子目录为艺人目录
        subs = os.listdir(path_dir)
        for sub in subs :
            path_artist = os.path.join(path_dir, sub)
            if os.path.isdir(path_artist) :
                analysis_dir_name(path_artist, 1, sub, aa_dict)
    elif mode == 1 :        #艺人目录
        ignore_name = False
        if artist_name != '' :
            sub_name_score = sub_dirs_has_text(path_dir, artist_name)
            print('目录{}的子目录艺人名分值为{}.'.format(path_dir, sub_name_score))
            if sub_name_score >= 0.3 :
                ignore_name = True
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
                if os.path.isdir(path_sort) :
                    analysis_dir_name(path_sort, 2, artist_name, aa_dict, ignore_name)
            else :
                path_album = os.path.join(path_dir, sub)
                if os.path.isdir(path_album) :
                    analysis_dir_name(path_album, 2 if sorted else 3, artist_name, aa_dict, ignore_name)    
    elif mode == 2 :    #分类目录
        ignore_name = False
        if artist_name != '' :
            sub_name_score = sub_dirs_has_text(path_dir, artist_name)
            print('目录{}的子目录艺人名分值为{}.'.format(path_dir, sub_name_score))
            if sub_name_score >= 0.3 :
                ignore_name = True

        sorted = sub_dirs_is_sort(path_dir)
        subs = os.listdir(path_dir)
        for sub in subs :
            path_album = os.path.join(path_dir, sub)
            if os.path.isdir(path_album) :
                analysis_dir_name(path_album, 2 if sorted else 3, artist_name, aa_dict, ignore_name)
    else :
        print('参数异常：path_dir={}, mode={}, artist={}.'.format(path_dir, mode, artist_name))
    return

def test_rip_info_from_dir_name() :
    path_log = get_log_path()
    str_now = datetime.strftime(datetime.now(), '%Y-%m-%d %H-%M-%S')
    file_name = 'log_{}.txt'.format(str_now)
    file_log = os.path.join(path_log, file_name)
    log_obj = open(file_log, 'w+', encoding='utf-8')
    sys.stdout = log_obj

    data = 'The Man Who Sold The World (2020 Mix) - Single'
    data = 'David Bowie - Nothing has changed (The Very Best of Bowie) [3CD] - 2014 [FLAC] [EP]'
    SPLITTERS = r'(-|\(|\)|\[|\])\s*'
    '''
    dl = re.split(SPLITTERS, data)
    for d in dl :
        if d is not None and d.strip() != '' :
            print(d)
    return
    '''
    artist_name = ''
    root = 'Y:\\MUSES\\华语女艺人'
    root = 'Y:\\MUSES\\欧美女艺人'
    #artist_name = os.path.basename(root)
    #root = 'Y:\\MUSES\\华语女艺人\\蔡健雅'
    #artist_name = os.path.basename(root)
    #root = 'Y:\\MUSES\\欧美乐队\\Black Box Recorder'
    #artist_name = os.path.basename(root)
    #root = 'Y:\\MUSES\\欧美男艺人\\David Bowie'
    #artist_name = os.path.basename(root)
    root_mode = 0
    artist_albums = dict()
    analysis_dir_name(root, root_mode, artist_name, artist_albums)
    dir_name = os.path.basename(root)
    export_json(dir_name, artist_albums)


    print('字典中共有({})个艺人信息。'.format(len(artist_albums)))
    for an in artist_albums :
        ai = artist_albums[an]
        print('艺人{}字典共有{}条key.'.format(an, len(ai)))
        for k in ai :
            print('found key={}.'.format(k))
            print(ai[k])


        if KEY_NAME_ARTIST_DIR in ai :
            ar = ai[KEY_NAME_ARTIST_DIR]
            print('艺人({})的根目录={}...'.format(an, ar))
        else :
            print('异常：艺人({})没有根目录。'.format(an))

        if KEY_NAME_ALBUMS in ai :
            albums = ai[KEY_NAME_ALBUMS]
            for ap in albums :
                title = albums[ap]
                print('  专辑标准名：{}, 目录={}.'.format(title, ap))
        else :
            print('异常：艺人({})没有专辑列表。'.format(an))

    return

    dirs = os.listdir(root)
    for dir in dirs :
        path_dir = os.path.join(root, dir)
        rip_info_from_dir_name(path_dir, artist_name)
    return

#test_rip_info_from_dir_name()