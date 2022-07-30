import os
from PIL import Image

COVER_IMAGES = ('folder.jpg', 'front.jpg', 'cover.jpg', )

def get_image_size(image_file : str) -> tuple[int, int] :
    img = Image.open(image_file)
    if img is not None :
        #w = img.width       #图片的宽
        #h = img.height      #图片的高
        #f = img.format      #图像格式
        return img.size
    else :
        return (0, 0)
