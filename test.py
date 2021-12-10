import yfinance as yf
import pandas as pd
import lxml
from lxml import html
import requests
import json
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import chromedriver_binary
import time
from selenium.webdriver.common.keys import Keys
import pandas as pd
from IPython.display import display
import re


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'close',
    'DNT': '1', # Do Not Track Request Header 
    'Pragma': 'no-cache',
    'Referrer': 'https://google.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

fin_url = 'https://finance.yahoo.com/quote/LLC.AX/financials?p=LLC.AX'
profile_url = 'https://finance.yahoo.com/quote/LLC.AX/profile?p=LLC.AX'

response = requests.get(profile_url, headers=headers)
soup = bs(response.text, 'html.parser')
pattern = re.compile(r'\s--\sData\s--\s')
script_data = soup.find('script', text=pattern).contents[0]
start = script_data.find("context")-2
json_data = json.loads(script_data[start:-12])
