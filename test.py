import pandas as pd
from lxml import html
from lxml import etree
import requests
import json
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import chromedriver_binary
import time
import re
import numpy as np
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pprint import pprint
import pickle


def main():
    url = 'https://www.capitaliq.com/ciqdotnet/login-sso.aspx'
    driver = webdriver.Chrome()
    driver.get(url)

    # login
    # pickle.dump(driver.get_cookies(), open('cookies.pkl', 'wb'))

    cookies = pickle.load(open('cookies.pkl', 'rb'))
    for cookie in cookies:
        driver.add_cookie(cookie)
        
    driver.get('https://www.capitaliq.com/CIQDotNet/my/dashboard.aspx')

    search_bar = driver.find_element_by_name("SearchText")
    
    url = 'https://estateinnovation.com/101-top-australia-construction-companies-and-startups-innovating-the-industry/'
    response = requests.get(url)
    soup = bs(response.content, 'html.parser')
    dom = etree.HTML(str(soup))
    companies = dom.xpath('//div[@class="wp-block-cover alignwide has-black-background-color has-background-dim is-position-center-center"]')

    company_data = []

    for company in companies:
        data = {}
        name = company.xpath('.//h3[@class="has-huge-font-size"]//descendant::span//text()')[0]
        links = dict(zip(company.xpath('.//a/text()'), company.xpath('.//a/@href')))
        data["Name"] = name 
        for link in links:
            data[link] = links[link]
            
        try:
            search_bar.send_keys(name)
            search_bar.send_keys(Keys.ENTER)