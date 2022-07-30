import os
from mutagen.flac import Picture, FLAC

import image_helper

def _print(audio : FLAC) :
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

def _add_cover(audio : FLAC, cover_file : str) :
   
    img_size = image_helper.get_image_size(cover_file)
    print('image width={}, height={}.'.format(img_size[0], img_size[1]))

    image = Picture()
    image.type = 3
    if cover_file.endswith('png'):
        image.mime = 'image/png'
    else:
        image.mime = 'image/jpeg'
    image.desc = 'front cover'
    image.width = img_size[0]
    image.height = img_size[1]
    with open(cover_file, 'rb') as f: # better than open(albumart, 'rb').read() ?
        image.data = f.read()
    audio.add_picture(image)
    return

def test_flac_tag() :

    file_name = 'Y:\\MUSES\\迪斯科\\港版荷东\\港版荷东精选(2CD)\\港版荷东精选02.flac\\05 - I Find The Way-Roger Meno.flac'
    file_name = 'Y:\\MUSES\\华语女艺人\\蔡健雅\\2003蔡健雅-[陌生人]专辑(WAV)\\06. 陌生人.flac'

    dir_name = os.path.dirname(file_name)
    cover_file = os.path.join(dir_name, 'front.jpg')
    audio = FLAC(file_name)
    _print(audio)
    #_add_cover(audio, cover_file)
    audio.save()
    return

test_flac_tag()