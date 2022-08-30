#from mutagen.mp3 import MP3
#from mutagen.id3 import ID3, APIC, error
import mutagen
from mutagen.flac import Picture, FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, error
import os

def _update_tag(file_name : str) :
    print('_update_tag call...')
    if not os.path.exists(file_name) :
        print('file not exist.')
        return
    at = mutagen.File(file_name)
    if at is None :
        print('file type is None.')
        return
    print(at)
    at.info.pprint()
    at.pprint()
    return

def flac_tag_handle(file_name : str) :
    audio = FLAC(file_name)
    #print(audio)
    info = audio.pprint()
    print(info)
    # add ID3 tag if it doesn't exist
    try:
        #audio.add_tags()
        pass
    except error:
        pass
    file_path = os.path.dirname(file_name)
    poster_file = os.path.join(file_path, 'folder.jpg')

    image = Picture()
    image.type = 3
    if poster_file.endswith('png'):
        image.mime = 'image/png'
    else:
        image.mime = 'image/jpeg'
    image.desc = 'front cover'
    with open(poster_file, 'rb') as f: # better than open(albumart, 'rb').read() ?
        image.data = f.read()
    
    audio.add_picture(image)
    audio.save()
    return

def test_mp3_file() :
    file_name = 'Y:\\MUSES\\华语男艺人\\罗大佑\\罗大佑 - 2005.香港搞搞真意思演唱会.mp3\\04 - 爱人同志 (Live).mp3'
    audio = MP3(file_name)

    print('开始打印metadata...')
    # Printing the metadata
    print(audio.pprint())
    print('打印metadata结束.')


    #_update_tag(file_name)
    #flac_tag_handle(file_name)
    return

test_mp3_file()