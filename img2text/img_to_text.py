import os
from PIL import Image
import pytesseract
import requests
from io import BytesIO
from langdetect import detect
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\PC\.conda\envs\scraping-env\Library\bin\tesseract.exe'
os.putenv('TESSDATA_PREFIX', r'C:\Program Files\Tesseract-OCR\tessdata')


def convert_img_to_text(img_path):
    # #url="https://instagram.fagc1-1.fna.fbcdn.net/v/t51.2885-15/332943419_515332940795930_6412412018861216025_n.jpg?stp=dst-jpg_e35_s640x640_sh0.08&_nc_ht=instagram.fagc1-1.fna.fbcdn.net&_nc_cat=102&_nc_ohc=quU9ARJrQekAX_fyH50&edm=AKEQFekBAAAA&ccb=7-5&oh=00_AfC-dMR2waKDwNfAlY02pIUHDfecXiLN_a1gEd-KxbjZ3g&oe=649B9250&_nc_sid=1349e3"
    # response = requests.get(url)
    # img = Image.open(BytesIO(response.content))
    script = ''
    if os.path.isfile(img_path):
        img = Image.open(img_path)
        osd = pytesseract.image_to_osd(img)
        lng = re.search("Script: ([a-zA-Z]+)\n", osd).group(1)
        di = {'Arabic': 'ara', 'Latin': 'eng'}
        script = pytesseract.image_to_string(img, lang=di[lng])

        return script


#
# url = "https://instagram.fagc1-1.fna.fbcdn.net/v/t51.2885-15/332943419_515332940795930_6412412018861216025_n.jpg?stp=dst-jpg_e35_s640x640_sh0.08&_nc_ht=instagram.fagc1-1.fna.fbcdn.net&_nc_cat=102&_nc_ohc=quU9ARJrQekAX_fyH50&edm=AKEQFekBAAAA&ccb=7-5&oh=00_AfC-dMR2waKDwNfAlY02pIUHDfecXiLN_a1gEd-KxbjZ3g&oe=649B9250&_nc_sid=1349e3"
# url2='https://i.ytimg.com/vi/CZCfTX-oRzg/hqdefault.jpg'
# print(convert_img_to_text(url))
