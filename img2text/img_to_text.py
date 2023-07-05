import os
from PIL import Image, ImageOps
import pytesseract
import requests
from io import BytesIO
from langdetect import detect
import re
import cv2
import numpy as np

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\PC\.conda\envs\scraping-env\Library\bin\tesseract.exe'
os.putenv('TESSDATA_PREFIX', r'C:\Program Files\Tesseract-OCR\tessdata')


def clean_str(text):
    search = ["أ", "إ", "آ", "ة", "_", "-", "/", ".", "،", " و ", " يا ", '"', "ـ", "'", "ى", '\ ', '\n', '\t', '"',
              '?', '؟', '!', '(', ')','@','\u200e','\u200f','١','©','#']
    replace = ["ا", "ا", "ا", "ه", " ", " ", "", "", "", " و", " يا", "", "", "", "ي", "", ' ', ' ', ' ', ' ? ', ' ؟ ',
               ' ! ', ' ', ' ',' ','','','','','']

    # Remove tashkeel
    p_tashkeel = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(p_tashkeel, "", text)

    # Remove longation eg, (....)
    p_longation = re.compile(r'(.)\1+')
    subst = r"\1\1"
    text = re.sub(p_longation, subst, text)

    text = text.replace('وو', 'و')
    text = text.replace('يي', 'ي')
    text = text.replace('اا', 'ا')
    text = text.replace('  ', ' ')
    text = re.sub(r'[^\S\r\n]{2,}', ' ', text)
    for i in range(0, len(search)):
        text = text.replace(search[i], replace[i])

    # Trim
    text = text.strip()

    return text
def convert_img_to_text(img_path):
    # #url="https://instagram.fagc1-1.fna.fbcdn.net/v/t51.2885-15/332943419_515332940795930_6412412018861216025_n.jpg?stp=dst-jpg_e35_s640x640_sh0.08&_nc_ht=instagram.fagc1-1.fna.fbcdn.net&_nc_cat=102&_nc_ohc=quU9ARJrQekAX_fyH50&edm=AKEQFekBAAAA&ccb=7-5&oh=00_AfC-dMR2waKDwNfAlY02pIUHDfecXiLN_a1gEd-KxbjZ3g&oe=649B9250&_nc_sid=1349e3"
    # response = requests.get(url)
    # img = Image.open(BytesIO(response.content))
    script = ''
    if os.path.isfile(img_path):
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        img = cv2.resize(img, None, fx=1.2, fy=1.2, interpolation=cv2.INTER_CUBIC)
        img = cv2.bilateralFilter(img,9,75,75)
        img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)

        # img = Image.open(img_path)
        # # applying grayscale method
        # gray = ImageOps.grayscale(img)

        # print(img.info)
        # osd = pytesseract.image_to_osd(img_path, config='--dpi ' + str(img.info['dpi'][0]))
        try:
            osd = pytesseract.image_to_osd(img)
            lng = re.search("Script: ([a-zA-Z]+)\n", osd).group(1)
            langs = {'Arabic': 'ara', 'Latin': 'eng'}
            if lng not in langs.keys():
                lng = "Arabic"
            script = pytesseract.image_to_string(img, lang=langs[lng])
        except Exception as e:
            script =''
        script = clean_str(script)
        if script is None:
            script=''

        return script


# def convert_with_vision(img_path):
#     def detect_document(path):
#         """Detects document features in an image."""
#         from google.cloud import vision
#
#         client = vision.ImageAnnotatorClient()
#
#         with open(path, "rb") as image_file:
#             content = image_file.read()
#
#         image = vision.Image(content=content)
#
#         response = client.document_text_detection(image=image)
#
#         for page in response.full_text_annotation.pages:
#             for block in page.blocks:
#                 print(f"\nBlock confidence: {block.confidence}\n")
#
#                 for paragraph in block.paragraphs:
#                     print("Paragraph confidence: {}".format(paragraph.confidence))
#
#                     for word in paragraph.words:
#                         word_text = "".join([symbol.text for symbol in word.symbols])
#                         print(
#                             "Word text: {} (confidence: {})".format(
#                                 word_text, word.confidence
#                             )
#                         )
#
#                         for symbol in word.symbols:
#                             print(
#                                 "\tSymbol: {} (confidence: {})".format(
#                                     symbol.text, symbol.confidence
#                                 )
#                             )
#
#         if response.error.message:
#             raise Exception(
#                 "{}\nFor more info on error messages, check: "
#                 "https://cloud.google.com/apis/design/errors".format(response.error.message)
#             )

#
# url = "https://instagram.fagc1-1.fna.fbcdn.net/v/t51.2885-15/332943419_515332940795930_6412412018861216025_n.jpg?stp=dst-jpg_e35_s640x640_sh0.08&_nc_ht=instagram.fagc1-1.fna.fbcdn.net&_nc_cat=102&_nc_ohc=quU9ARJrQekAX_fyH50&edm=AKEQFekBAAAA&ccb=7-5&oh=00_AfC-dMR2waKDwNfAlY02pIUHDfecXiLN_a1gEd-KxbjZ3g&oe=649B9250&_nc_sid=1349e3"
# url2='https://i.ytimg.com/vi/CZCfTX-oRzg/hqdefault.jpg'
# url4 = r"../frontend/src/assets/temp/images/2921893318822540978.png"
# res = convert_img_to_text(url4)
# print(res)
# cv2.imshow('', res[1])
# cv2.waitKey(0)
