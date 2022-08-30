import os
import sys
from mutagen.flac import Picture, FLAC

import image_helper
import tag_helper

PIC_TYPE = ('.bmp', '.png', '.jpg', '.jpeg', )
COVER_NAMES = ('front cover', 'cover', 'other', )
MIN_COVER_SIZE = (600, 600, )

class flac_tag(tag_helper.tag_info) :
    def __init__(self) -> None:
        super().__init__()
        #FLAC only
        self.ISRC = ''              #全球ISRC唯一编码
        return
    #从flac文件载入metadata 
    def load(self, audio : FLAC) : 
        self.title = audio.tags['TITLE']
        self.artist_name = audio.tags['ARTIST']
        self.album_artist = audio.tags['ALBUMARTIST']
        self.album_name = audio.tags['ALBUM']
        self.track = audio.tags['TRACKNUMBER']
        self.year = audio.tags['DATE']
        self.genre = audio.tags['GENRE']
        self.disc_serial = audio.tags['DISCNUMBER']
        self.track_count = audio.tags['TRACKTOTAL']
        self.comment = audio.tags['COMMENT']
        #FLAC only
        self.ISRC = audio.tags['ISRC']
        return
    def save(self, audio : FLAC) :
        audio.tags['TITLE'] = self.title
        if self.is_same_artist() :
            audio.tags['ARTIST'] = self.get_play_artist()
            audio.tags['ALBUMARTIST'] = ''
        else :
            audio.tags['ARTIST'] = self.get_play_artist()
            audio.tags['ALBUMARTIST'] = self.get_album_artist()
        audio.tags['ALBUM'] = self.album_name
        audio.tags['TRACKNUMBER'] = self.track
        #audio.tags['DATE'] = sel
        return

def print_flac_tags(audio : FLAC) :
    print(audio)
    if 'title' in audio :
        print('found title tag, value={}.'.format(audio['title']))
        audio['title'] = '不是陌生人'

    pics = audio.pictures
    if pics is not None :
        count = len(pics)
        print('pic count = {}.'.format(count))
        for pic in pics :
            print(pic.type)         #type=3(COVER_FRONT), mime=image/jpeg, desc=front cover
            print(pic.mime)
            print(pic.desc)
            print(len(pic.data))
            print(pic.width)
            print(pic.height)
    if 'covr' in audio :
        print('found covr tag in tags.')
    if 'APIC:' in audio :
        print('found APIC tag in tags.')

    return

#获取图片信息
def _get_pic_info(audio : FLAC) :
    pics = audio.pictures()
    for pic in pics :
        type = pic.type
        mime = pic.mime
        desc = pic.desc
    return

#判断一个图片对象是否封面图片
def _is_cover_pic(p : Picture) -> bool :
    is_cover = False
    if p.desc.lower().strip() in COVER_NAMES :
        is_cover = True
    return is_cover

def get_cover_pic(audio : FLAC) -> Picture :
    pic = None
    pics = audio.pictures()
    if pics is None or len(pics) == 0 :
        return None
    if len(pics) == 1 :
        pic = pics[0]
    else :
        for p in pics :
            if _is_cover_pic(p) :
                pic = p
                break    
    return pic

#返回内嵌封面图片的数据大小信息（长，宽，数据流大小），没有封面图片则返回None
def get_cover_size(audio : FLAC) -> tuple :
    pic = get_cover_pic(audio)
    if pic is None :
        return None
    else :
        return (pic.width, pic.height, len(pic.data))

#删除所有的图片
def _del_pics(audio : FLAC) :
    audio.clear_pictures()
    return

#加入封面图片
#audio : flac文件对象
#cover_file : jpg/png图片文件（全路径）
def _add_cover(audio : FLAC, cover_file : str) :
    img_size = image_helper.get_image_size(cover_file)
    print('image width={}, height={}.'.format(img_size[0], img_size[1]))

    image = Picture()
    image.type = 3
    if cover_file.lower().endswith('.png') :
        image.mime = 'image/png'
    elif cover_file.lower().endswith('.jpg') or cover_file.lower().endswith('.jpeg') :
        image.mime = 'image/jpeg'
    else :  #别的格式不处理
        return
    image.desc = 'front cover'
    image.width = img_size[0]
    image.height = img_size[1]
    with open(cover_file, 'rb') as f: # better than open(albumart, 'rb').read() ?
        image.data = f.read()
    audio.add_picture(image)
    return

def get_tag_info(audio : FLAC) -> tag_helper.tag_info :
    info = None
    #audio.tags['YEAR']
    return info

def test_flac_tag() :
    print('test flac tag...')
    file_name = 'Y:\\MUSES\\迪斯科\\港版荷东\\港版荷东精选(2CD)\\港版荷东精选02.flac\\05 - I Find The Way-Roger Meno.flac'
    file_name = 'Y:\\MUSES\\华语女艺人\\蔡健雅\\2003 -[陌生人]专辑(WAV)\\06. 陌生人.flac'

    dir_name = os.path.dirname(file_name)
    cover_file = os.path.join(dir_name, 'front.jpg')
    audio = FLAC(file_name)

    print('开始打印metadata...')
    # Printing the metadata
    print(audio.pprint())
    print('打印metadata结束.')
    #return

    #print_flac_tags(audio)
    #_add_cover(audio, cover_file)
    #audio.save()
    return

test_flac_tag()