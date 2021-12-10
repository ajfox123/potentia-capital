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



def main():
    li_driver = webdriver.Chrome()
    li_driver.get("https://www.linkedin.com/")
    
    yh_driver = webdriver.Chrome()
    yh_driver.get("https://finance.yahoo.com/")
    
    username_box = li_driver.find_element_by_id("session_key")
    #username = input("LinkedIN Username: ")
    username = 'ajfox123@gmail.com'
    username_box.send_keys(username)
    
    password_box = li_driver.find_element_by_id("session_password")
    #password = input("LinkedIN Password: ")
    password = 'Loopytro0L!'
    password_box.send_keys(password)
    
    login_button = li_driver.find_element_by_class_name("sign-in-form__submit-button")
    login_button.click()

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
            
        if (data["Linkedin"] != ''):
            li_data = linkedin_data(data["Linkedin"], li_driver)
            if li_data:
                data = {**data, **li_data}
        
        try:
            yh_data = yahoo_data(name, yh_driver)
            data = {**data, **yh_data}
        except:
            print('yh page not found')
        company_data.append(data)
        
        
    df = pd.DataFrame(company_data)
    df.to_csv("company_data.csv", index=False)



def linkedin_data(linkedin_url, driver):
    data = {}
    
    driver.get(linkedin_url)
    
    # Some pages redirect, so we wait for that with a time.sleep()
    time.sleep(0.5)
    url = driver.current_url
    
    # Deal with misformatted linkedin links
    if 'company' not in url:
        url = str("https://www.linkedin.com/company/" + url[url.index('.com')+5:])
    if 'about' in url:
        url = url.replace('/about', '')
    if url[-1] != '/':
        url = url[:url.rindex('?')]

    # Get general about page information
    about_url = str(url+'about/') if url[-1] == '/' else str(url+'/about/')
    driver.get(about_url)
    if 'This page doesn’t exist' in driver.page_source:
        print(f'page doesnt exist @ {about_url}')
        return {"Linkedin": ""}
        
    data["Linkedin"] = url
    
    try:
        els = driver.find_elements_by_xpath('//dt[@class="mb1 text-heading-small"]')
    
        for i in els:
            el_info = i.find_element_by_xpath('./following-sibling::dd[1]')
            if i.text == "Phone":
                data[i.text] = el_info.text.split("\n")[0]
            else:
                data[i.text] = el_info.text
    except:
        print(f"No linkedin info found on {about_url}")
        return
    
    # Get office number information
    try:
        locations = driver.find_element_by_xpath('.//div[@class="ember-view artdeco-card p0 mb4"]').text
        locations = locations[locations.index('(')+1:locations.index(')')]
        data["Offices"] = locations
    except:
        print(f"No office info found on {about_url}")

    return data



def yahoo_data(name, driver):
    data = {}
    
    driver.get("https://finance.yahoo.com/")
    time.sleep(0.5)
    search_bar = driver.find_element_by_name("yfin-usr-qry")
    search_bar.send_keys(name)
    search_bar.send_keys(Keys.ENTER)
    
    time.sleep(1)
    url = driver.current_url
    stock = 'quote' in url
        
    
    if stock:
        url = url.split('?')[0]
        ticker = url[url.rindex('/')+1:]
        fin_url = url+'/financials?p='+ticker
        profile_url = fin_url.replace('financials', 'profile')
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'close',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Referrer': 'https://google.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
        }

        try:
            response = requests.get(profile_url, headers=headers)
            time.sleep(0.5)
            soup = bs(response.text, 'html.parser')
            pattern = re.compile(r'\s--\sData\s--\s')
            script_data = soup.find('script', text=pattern).contents[0]
            start = script_data.find("context")-2
            json_data = json.loads(script_data[start:-12])
            d = json_data['context']['dispatcher']['stores']['QuoteSummaryStore']['assetProfile']['companyOfficers']
            execs = pd.DataFrame(d)
            execs['title'] = execs['title'].str.upper().str.replace(',', ' ')
            try:
                ceo = execs[execs.title.apply(lambda x: any(identifier in x for identifier in ['CEO', 'CHIEF EXECUTIVE OFFICER', "CHIEF EXEC. OFFICER"]))].name.values[0]
                data['CEO'] = ceo
                print(ceo)
            except:
                print('ceo not found')
            try:
                cfo = execs[execs.title.apply(lambda x: any(identifier in x for identifier in ['CFO', 'CHIEF FINANCIAL OFFICER']))].name.values[0]
                data['CFO'] = cfo
                print(cfo)
            except:
                print('cfo not found')
            try:
                cto = execs[execs.title.apply(lambda x: any(identifier in x.replace('DIRECTOR', '') for identifier in ['CTO', 'CHIEF TECHNOLOGY OFFICER']))].name.values[0]
                data['CTO'] = cto
                print(cto)
            except:
                print('cto not found')
        except:
            print(f'execs not found {profile_url}')

        try:
            response = requests.get(fin_url, headers=headers)
            time.sleep(0.5)
            tree = html.fromstring(response.content)
            table_rows = tree.xpath("//div[contains(@class, 'D(tbr)')]")

            parsed_rows = []
            for table_row in table_rows:
                parsed_row = []
                el = table_row.xpath("./div")

                none_count = 0

                for rs in el:
                    try:
                        (text,) = rs.xpath('.//span/text()[1]')
                        parsed_row.append(text)
                    except ValueError:
                        parsed_row.append(np.NaN)
                        none_count += 1

                if (none_count < 4):
                    parsed_rows.append(parsed_row)

            financials = pd.DataFrame(parsed_rows)
            financials.columns = financials.iloc[0]
            financials = financials[1:]
            financials.iloc[:, 1:] = financials.iloc[:, 1:].apply(lambda x: x.str.replace(',', '').astype(float)*1000, axis=1)
            revenue = financials[financials.Breakdown.str.match("Total Revenue")].values[0][1]
            ebitda = financials[financials.Breakdown.str.match("Normalized EBITDA")].values[0][1]
            data['Revenue'] = revenue
            data['EBITDA'] = ebitda
        except:
            print(f'financials not found {fin_url}')
    else:
        print(url, 'is not public')
        
    return data
    
    
    
main()