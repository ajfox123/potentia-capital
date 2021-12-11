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
        print(name)
        for link in links:
            data[link] = links[link]
        
        driver.get('https://www.capitaliq.com/CIQDotNet/my/dashboard.aspx')
        found = find_company_page(name, driver)
        if found:
            print('found company')
            iq_data = scrape_iq_data(driver)
            data = {**data, **iq_data}
        else:
            print('not found')
        company_data.append(data)
        print('\n')
        
    df = pd.DataFrame(company_data)
    df.to_csv("company_data_NEW.csv", index=False)
        
        
            
def find_company_page(name, driver):
    search_bar = driver.find_element_by_name("SearchText")
    search_bar.send_keys(name)
    search_bar.send_keys(Keys.ENTER)
    
    if 'company' in driver.current_url:
        # On company page
        return True

    elif 'Please see some suggested matches:' in driver.page_source:
        # Pick from suggestion
        company_suggestions = driver.find_elements_by_xpath('//table//*[contains(text(), "Company)")]')
        print('going through suggestions')
        try:
            for i in range(min(5, len(company_suggestions))):
                href = company_suggestions[i]
                print('trying:    ', href.text)
                href.click()
                offices = driver.find_element_by_xpath('//a[contains(text(), "View All Office Addresses")]')
                primary_office = offices.find_element_by_xpath('./../../../../following-sibling::*').text.split('\n')[0]
                if 'Australia' in primary_office:
                    return True
                else:
                    driver.back()
                    company_suggestions = driver.find_elements_by_xpath('//table//*[contains(text(), "Company)")]')
            print(f'not found in first few links')
            return False
            
        except:
            print('need to debug')
            time.sleep(5)
    else:
        company_suggestions = driver.find_elements_by_xpath('//table[@class="cTblListBody"]//*[@href]')
        print('going through search results')
        try:
            for i in range(min(5, len(company_suggestions))):
                href = company_suggestions[i]
                print('trying:    ', href.text)
                href.click()
                offices = driver.find_element_by_xpath('//a[contains(text(), "View All Office Addresses")]')
                primary_office = offices.find_element_by_xpath('./../../../../following-sibling::*').text.split('\n')[0]
                if 'Australia' in primary_office:
                    return True
                else:
                    driver.back()
                    company_suggestions = driver.find_elements_by_xpath('//table[@class="cTblListBody"]//*[@href]')
            return False
        except:
            time.sleep(5)
            print('need to debug')
            return False



def scrape_iq_data(driver):
    data = {}
    revenue = driver.find_element_by_xpath('//td//*[contains(text(), "Total Revenue")]').find_element_by_xpath('..//following-sibling::td').text
    try:
        revenue = float(revenue.replace(",", ""))*(10**6)
    except:
        revenue = None
    data['Revenue'] = revenue
    
    ebitda = driver.find_element_by_xpath('//td//*[contains(text(), "EBITDA")]').find_element_by_xpath('..//following-sibling::td').text
    try:
        ebitda = float(ebitda.replace(",", ""))*(10**6)
    except:
        ebitda = None
    data['EBITDA'] = ebitda
    
    d = pd.read_html(driver.page_source)
    for df in d[::-1]:
        if 'Key Professionals View All' in df.values:
            execs = df.rename(columns=df.iloc[1]).drop(df.index[:2]).reset_index(drop=True).iloc[:, :2]
            execs['Title'] = execs['Title'].str.upper().str.replace(',', ' ')
            try:
                ceo = execs[execs.Title.apply(lambda x: any(identifier in x for identifier in ['CEO', 'CHIEF EXECUTIVE OFFICER', "CHIEF EXEC. OFFICER"]))].Name.values[0]
                data['CEO'] = ceo
                print(ceo)
            except:
                print('ceo not found')
            try:
                cfo = execs[execs.Title.apply(lambda x: any(identifier in x for identifier in ['CFO', 'CHIEF FINANCIAL OFFICER']))].Name.values[0]
                data['CFO'] = cfo
                print(cfo)
            except:
                print('cfo not found')
            try:
                cto = execs[execs.Title.apply(lambda x: any(identifier in x.replace('DIRECTOR', '') for identifier in ['CTO', 'CHIEF TECHNOLOGY OFFICER']))].Name.values[0]
                data['CTO'] = cto
                print(cto)
            except:
                print('cto not found')
            break
    return data
main()