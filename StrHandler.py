# -*- coding: UTF-8 -*-

from lib2to3.pgen2.token import NAME
import sys
import os
from datetime import datetime 
import re
import string
import pypinyin

import langconv
import functools

import langid

OLD_WORD_MAP = ( ('実', '实'), ('亜', '亚'), ('桜', '樱'), ('咲', '笑'), ('嶋', '岛'), ('栞', '刊'), ('篠', '小'), ('笹', '屉'), ('澪', '零'), ('冨', '富'), ('瀬', '濑'), ('沢', '泽'), ('岡', '冈') , ('倖', '幸'), ('凪', '止'), ('広', '广'),  \
    ('歩', '步'), ('絵', '绘'), ('雫', '霞'), ('糸', '丝'), ('笹', '屉'), ('斉', '齐'), ('巻', '卷'), ('笕', '见'), ('砥', '抵'), ('槇', '滇'), ('槙', '滇'), ('樋', '通'), ('榊', '神'), ('榎', '加'), ('椿', '春'), ('滝', '龙'), ('眞', '真'), ('栄', '荣'), ('裏', '里'), \
    ('刈', '义'), ('槻', '规'), ('掛', '挂'), ('佐々木', '佐佐木') )

def name_chs_format(name) :
    format = name
    for OL in OLD_WORD_MAP :
        format = format.replace(OL[0], OL[1])
    foramt = cht_to_chs(format)
    return format


# 转换繁体到简体
def cht_to_chs(str) :
    line = langconv.Converter('zh-hans').convert(str)
    line.encode('utf-8')
    return line

def _is_chs_or_eng(str) :
    failed = False
    for c in str :
        if ord(c) < 128 :
            continue
        elif is_char_chinese(c) :
            continue
        else :
            failed = True
            break
    return not failed

#判断一个字符串是否全部为英文
def is_pure_eng(str) :
    return all(ord(c) < 128 for c in str)

#字符串包含日韩文
def is_contains_jap(str) :
    # \uAC00-\uD7A3为匹配韩文的，其余为日文
    jap = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7A3]') 
    return jap.search(str) != None

def is_ascii_controler(c) :
    controler = False
    if ord(c) >= 0 and ord(c) <= 64 :
        controler = True
    elif ord(c) >= 91 and ord(c) <= 96 :
        controler = True
    elif ord(c) >= 123 and ord(c) <= 127 :
        controler = True
    return controler

def is_symbol(c) :
    symbol = False
    ENG_SYMBOL = string.punctuation
    CHS_SYMBOL = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.。'
    if c in ENG_SYMBOL :
        symbol = True
    elif c in CHS_SYMBOL :
        symbol = True
    return symbol

def is_char_chinese(c) :
    ZH_SYMBOLS = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.。'
    is_zh = False
    if '\u4e00' <= c <= '\u9fa5' :
        is_zh = True
    elif c in ZH_SYMBOLS :
        is_zh = True
    return is_zh

#字符串全部为中文
def is_all_chinese(str) :
    for _c in str:
        if not is_char_chinese(_c) :
            return False
    return True

#字符串包含中文
def is_contains_chinese(str) :
    for _c in str:
        if '\u4e00' <= _c <= '\u9fa5':
            return True
    return False    

#取得一个字符串中的英文比重，0-100
def get_eng_percent(str) :
    percent = 0
    count = len(str)
    eng_count = 0
    for c in str :
        if is_ascii_controler(c) :
            count -= 1
        elif (ord(c) >= 65 and ord(c) <= 90) or (ord(c) >= 97 and ord(c) <= 122) :
            eng_count += 1
    if count > 0 :
        percent = int(eng_count * 100 / count)
    #print('len=%d, count=%d, eng=%d.' %(len(str), count, eng_count))
    return percent    

#取得一个字符串中的中文比重，0-100
def get_zh_percent(str) :
    percent = 0
    count = len(str)
    zh_count = 0
    for c in str :
        if is_ascii_controler(c) :
            count -= 1
        elif is_char_chinese(c) :
            zh_count += 1
    if count > 0 :
        percent = int(zh_count * 100 / count)
    #print('len=%d, count=%d, zh=%d.' %(len(str), count, zh_count))
    return percent

def is_zh_or_eng(str) :
    if is_lang_zh(str, Percent=0.3) :
        return 1
    elif is_lang_eng(str) :
        return 2
    return 0

def is_lang_zh(str, Percent=0.8) :
    if str.strip() == '' :
        return False
    return float(get_zh_percent(str) / 100) >= Percent

def is_lang_eng(str, Percent=0.95) :
    if str.strip() == '' :
        return False
    return float(get_eng_percent(str) / 100)>= Percent

def rip_ass_sub_closed(str) :
    closed_table = {'}': '{', }
    return rip_str_closed(str, ClosedTable=closed_table)

def rip_ass_sub_closed_str(str) :
    list = rip_ass_sub_closed(str)
    result = ''
    for l in list :
        result += l + ' ' 
    return result.strip()

def rip_srt_sub_closed(str) :
    closed_table = {'}': '{', '>': '<', }
    return rip_str_closed(str, ClosedTable=closed_table)

def rip_srt_sub_closed_str(str) :
    list = rip_srt_sub_closed(str)
    result = ''
    for l in list :
        result += l + ' ' 
    return result.strip()

#删除字符串里的闭包数据
def rip_str_closed(str, ClosedTable=None) :
    texts = []
    CLOSE_DICT = {'}': '{', '>': '<', ']' : '[', ')' : '(', }
    if ClosedTable == None :
        ClosedTable = CLOSE_DICT
    begin = end = -1
    cps = []        #check points 
    for i in range(len(str)) :
        c = str[i]
        if c in ClosedTable.values() : #闭包开始标志
            if len(cps) == 0 :  #遇到一个最外层的开始标志
                #assert(begin >= 0)
                #print('find first closed, i=(%d), begin=(%d).' %(i, begin))
                if begin >= 0 :
                    text = str[begin:i]
                    #print('i=(%d), begin=(%d), text=(%s).' %(i, begin, text))
                    if text.strip() != '' :
                        texts.append(text)
                begin = -1
            cps.append(c)
        elif c in ClosedTable :      #闭包结束标志
            #print('find closed right, i=%d, begin=%d. before char=%s.' %(i, begin, str[i-1]))
            if len(cps) == 0 :      #没有开始标志，直接出来一个结束标志
                #assert(False)
                pass
            elif cps.pop() != ClosedTable[c] :   #跟最后一个压入的开始标志不匹配
                #闭合异常
                #assert(False)
                pass
        else :      #遇到普通字符
            if len(cps) == 0 and begin == -1 :
                begin = i
                #print('normal char=(%s), set begin from -1 to i=(%d).' %(c, i))

    #print('last begin=%d, len(cps)=%d...' %(begin, len(cps)))
    #if begin >= 0 and (begin+1) < len(str) :
    if begin >= 0 and (begin) < len(str) :
        text = str[begin:]
        #print('last check, begin=(%d), text=(%s).' %(begin, text))
        if text.strip() != '' :
            texts.append(text)
    if len(cps) != 0 :      #闭包没有遇到足够的关闭标志
        #assert(False)
        pass
    return texts


#判断字符串是否闭合
def is_str_closed(str):
    CLOSE_DICT = {'}': '{', '>': '<', ']' : '[', ')' : '(', }
    b = []
    flag = True
    for c in str:
        if c in CLOSE_DICT.values :
            b.append(c)
        elif c in CLOSE_DICT :
            if len(b) == 0 or b.pop() != CLOSE_DICT[c]:
                return False
    #判断最后列表b里面的左括号是否全部被弹出
    if len(b) != 0 :
        flag = False
    return flag

#取得字符串中第N个分隔符出现的位置
def get_N_index(info_str, spliter, n) :
    index = -1
    if n <= 0 :
        return -1
    count = 0
    begin = 0
    while True :
        index = info_str.find(spliter, begin)
        if index < 0 :
            break
        else :
            begin = index + 1
            count += 1
            if count >= n :
                break    
    return index

#删除一个字符串里的指定字符
#如esc_list=None，则删除字符串里的回车换行
def str_escape(str, esc_list=None) :
    DEFAULT_ESCAPE_LIST = ('\\n', '\\r', '\\r\\n', )
    if esc_list == None :
        esc_list = DEFAULT_ESCAPE_LIST
    new_str = str
    for e in esc_list :
        new_str = new_str.replace(e, '').replace(e.upper(), '')
    return new_str

#读入ini文件的一个session的全部行
def read_session(name, datas) :
    lines = []
    push = False
    for data in datas :
        check = data.strip()
        if check.lower().find(name.lower()) == 0 :
            push = True
        elif len(check) >= 2 and check[0] == '[' and check[-1] == ']' :
            if push :
                break
        else :
            if push and check != '' :
                lines.append(data)
    return lines


def get_entity(info_str) :
    SPLIT_FALGS = (':', '：', )
    entity = info_str
    for SF in SPLIT_FALGS :
        index = entity.find(SF)
        if index >= 0 :
            entity = entity[index+1:]
            break
    entity = get_first_name(entity)
    return entity

#把一个包含名字信息的字符串转换成名字列表
def name_info_to_names(info_str) :
    names = []
    CHS_BRACKETS = ('（', '）', )
    ENG_BRACKETS = ('(', ')', )
    SPLIT_FLAGS = (',', '，', '、', '/', '|')
    br_index = -1
    bl_index = info_str.find(CHS_BRACKETS[0])
    if bl_index >= 0 :
        br_index = info_str.find(CHS_BRACKETS[1])
    else :
        bl_index = info_str.find(ENG_BRACKETS[0])
        if bl_index >= 0 :
            br_index = info_str.find(ENG_BRACKETS[1])
    if bl_index > 0 :
        names.append(info_str[:bl_index])
        extend_str = info_str[bl_index + 1 : br_index]
        handled = False
        for SF in SPLIT_FLAGS :
            if SF in extend_str :
                alias_list = extend_str.split(SF)
                names.extend(alias_list)
                handled = True
                break
        if not handled :
            names.append(extend_str)    
    else :
        handled = False
        for SF in SPLIT_FLAGS :
            if SF in info_str :
                alias_list = info_str.split(SF)
                names.extend(alias_list)
                handled = True
                break
        if not handled :
            names.append(info_str)
    return names

#取得一个包含名字信息的字符串里的第一个名字
def get_first_name(info_str) :
    first = ''
    name_list = name_info_to_names(info_str)
    if len(name_list) > 0 :
        first = name_list[0]
    return first

#取得一个字符串里的数字个数
def get_number_count(info_str) :
    count = 0
    for c in info_str :
        if c.isdecimal() :
            count += 1
    return count

def name_2_pinyin(name : str, trans_num : bool = False) -> str :
    IGNORE_ENG_SYMBOL = string.punctuation
    IGNORE_CHS_SYMBOL = '！？｡＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.。'
    DIGITAL_MAP = ( ('0', 'L'), ('1', 'Y'), ('2', 'E'), ('3', 'S'), ('4', 'S'), ('5', 'W'), ('6', 'L'), ('7', 'Q'), ('8', 'B'), ('9', 'J') )
    def del_ignore(name) :
        clean = name
        for ies in IGNORE_ENG_SYMBOL :
            clean = clean.replace(ies, '')
        for ics in IGNORE_CHS_SYMBOL :
            clean = clean.replace(ics, '')
        return clean
    def digital_2_pinyin(str) :
        py = str
        for DM in DIGITAL_MAP :
            py = py.replace(DM[0], DM[1])
        return py
    def _add_word(w, flag, wl) :
        clean = del_ignore(w).strip()
        if clean != '' :
            if flag == 3 :              
                if not clean.isupper() :    #混合大小写的英文单词，取首字母
                    clean = clean[0]
            wl.append((clean, flag))
        return
    def _name_2_frags(name) :
        frags = list()
        cur = ''
        flag = 0            #=1中文，=2数字，=3英文。=4其它语种。=0开头或丢弃字符，如标点符号。
        for i in range(len(name)) :
            c = name[i]
            if c.isdigit() :    #数字
                #print('find digital=%s.' %c)
                if flag == 2 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 2
            #elif is_pure_eng(c) :   #英文字符
            elif c.encode().isalpha() :
                #print('find alpha=%s.' %c)
                if flag == 3 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 3
            elif is_all_chinese(c) :         #中文字符
                #print('found chs=%s.' %c)
                if flag == 1 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 1
            
            elif is_symbol(c) :              #无法识别的字符，如标点符号
                #print('found ignore char=%s.' %c)
                if flag != 0 :
                    _add_word(cur, flag, frags)
                    cur = ''
                    flag = 0
            else :          #无法识别的字符，日韩德等其它语种
                if flag == 4 :
                    cur = cur + c
                else :
                    if flag != 0 :
                        _add_word(cur, flag, frags)
                    cur = c
                    flag = 4
        if cur != '' and flag != 0 :            #最后一个词
            _add_word(cur, flag, frags)

        return frags

    py_list = list()
    frags = _name_2_frags(name)
    for f in frags :
        #print('data=%s, flag=%s.' %(f[0], f[1]))
        if f[1] == 1 :      #中文
            first_list = pypinyin.lazy_pinyin(f[0])
            first = ''
            for f in first_list :
                first += f[0].upper()
            py_list.append(first)
        elif f[1] == 2 :  #数字
            if trans_num :
                first = digital_2_pinyin(f[0])
            else :
                first = f[0]
            py_list.append(first)
        elif f[1] == 3 :    #英文
            first = f[0].upper()
            py_list.append(first)
        elif f[1] == 4 :    #其它语种，跟英语一样保留第一个字符
            first = f[0].upper()
            py_list.append(first)
    first_py = ''
    for py in py_list :
        first_py += py
    return first_py

#取得固定长度的拼音缩写
def get_fixed_PINYIN(data : str, fix_len : int) -> str :
    FULL_WITH = '0'
    fixed = ''
    assert(fix_len > 0)
    PY = name_2_pinyin(data)
    if len(PY) >= fix_len :
        fixed = PY[ : fix_len]
    else :
        fixed = PY.ljust(fix_len, FULL_WITH)
    return fixed

def test_get_n_index() :
    line = 'Dialogue: 0,0:02:04.20,0:02:06.28,Default,,0000,0000,0000,,我正在研究着什么?'
    index = get_N_index(line, ',', 9)
    print('pos of 9n = %d.' %(index))
    if index >= 0 and (index+1) < len(line) :
        print('next =(%s).' %(line[index+1]))
    return

def test_rip_str_closed() :
    MOVIES = ('索多玛120天.1974', '红色娘子军.1969', '悬疑', '三上悠亚', 'JULIA', '28.1999', )
    for m in MOVIES :
        is_chs = is_lang_zh(m)
        is_all = is_all_chinese(m)
        print('(%s)是否中文名=%s, %s.' %(m, is_chs, is_all))
    return

    str = '{{\\fn微软雅黑\\b1\\fs30\\shad0\\c&HB8A682&\\move(740,370,251,370)\\fade (255, 32, 224, 0, 500, 2000, 2200)}伯克利学校'
    str = '{\\pos(512.028,343.995)\\shad0\\c&H15191B&\\frz1.137\\3c&H404040&\\fn黑体\\fs30\\frx32\\fry0}2号摄像机'
    print('raw data=(%s).' %str)
    result = rip_srt_sub_closed_str(str)
    print(result)
    return


    now_t = datetime.now()
    str_now = datetime.strftime(now_t, '%H-%M-%S') 
    out_file = open('字幕信息' + str_now + '.txt', 'w+', encoding='utf-8')
    sys.stdout = out_file  #标准输出重定向至文件


    SRT_LINES = ('{\\fnMicrosoft YaHei\\fs17\\bord1\\shad1\\b0}来了  你要香肠  你要鸡蛋{\\r}{\\c&H62a8eb&\\fs13}if they wanna make out an exchange for a story.', \
        '{\\fnTahoma\\fs8\\bord1\\shad1\\1c&HC2E0EC&\\b0}Here you go. You got the sausage, pancakes for you,{\\r}', \
        '<font color=#ED935E>{\\fn微软雅黑\\fs25}热力来袭！', '<font><异常闭包{font size}迪尔茨', )
    for sl in SRT_LINES :
        print('原始行=(%s)...' %sl)
        texts = rip_str_closed(sl)
        print('萃取出%d个数据。' %(len(texts)))
        for t in texts :
            print('---数据：%s.' %(t))
    return

def test_py_sort() :
    s = 1
    e = 13
    
    info = 'S{:0>2d}E{:0>2d}'.format(s, e)
    print(info)
    jap2 = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\uAC00-\uD7A3]')  # \uAC00-\uD7A3为匹配韩文的，其余为日文

    NAMES = ('1984我爱，你ER', 'E.T', '做个勇敢中国', '大侦探波洛', 'The.Tragedy.of.Macbeth', '26种死法', '二十一克', '돌아오라 개구리소년', '東京リベンジャーズ', 'Händler der vier Jahreszeiten', )

    #NAMES = ('돌아오라 개구리소년', )
    for n in NAMES :
        py = name_2_pinyin(n)
        fix_3 = get_fixed_PINYIN(n, 3)
        print('名称=%s, 拼音=%s, 定长=%s.' %(n, py, fix_3))
    return

#test_get_n_index()
#test_rip_str_closed()
#test_py_sort()