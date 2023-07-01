import json
import re
import time
from urllib.request import urlopen

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup as bs
from pandas.io.json import json_normalize
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
username='beaute.coook'
browser = webdriver.Chrome('C:\dev\chromedriver')
browser.get('https://www.instagram.com/'+username+'/?hl=en')
Pagelength = browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#Extract links from user profile page
links=[]
source = browser.page_source
data=bs(source, 'html.parser')
body = data.find('body')
script = body.find('script', string=lambda t: t.startswith('window._sharedData'))
page_json = script.string.split(' = ', 1)[1].rstrip(';')
data = json.loads(page_json)
#try 'script.string' instead of script.text if you get error on index out of range
for link in data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']:
    links.append('https://www.instagram.com'+'/p/'+link['node']['shortcode']+'/')
#try with ['display_url'] instead of ['shortcode'] if you don't get links