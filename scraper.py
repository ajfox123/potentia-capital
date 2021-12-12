import pandas as pd
from lxml import html
from lxml import etree
import requests
import json
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import chromedriver_binary
import numpy as np
from selenium.webdriver.common.by import By
import pickle
from getpass import getpass
import time



def main():
    # Capiq driver
    url = 'https://www.capitaliq.com/ciqdotnet/login-sso.aspx'
    capiq_driver = webdriver.Chrome(executable_path=r'/Users/archiefox/Desktop/potentia-capital/chromedriver')
    capiq_driver.get(url)

    # login
    # pickle.dump(driver.get_cookies(), open('cookies.pkl', 'wb'))

    cookies = pickle.load(open('mac_cookies.pkl', 'rb'))
    for cookie in cookies:
        capiq_driver.add_cookie(cookie)

    # Linkedin driver
    li_driver = webdriver.Chrome(executable_path=r'/Users/archiefox/Desktop/potentia-capital/chromedriver')
    li_driver.get("https://www.linkedin.com/")
    username_box = li_driver.find_element_by_id("session_key")
    username ='ajfox123@gmail.com'
    username_box.send_keys(username)

    password_box = li_driver.find_element_by_id("session_password")
    password = getpass("LinkedIN Password: ")
    password_box.send_keys(password)

    login_button = li_driver.find_element_by_class_name("sign-in-form__submit-button")
    login_button.click()

    # Get companies and links
    url = 'https://estateinnovation.com/101-top-australia-construction-companies-and-startups-innovating-the-industry/'
    response = requests.get(url)
    soup = bs(response.content, 'html.parser')
    dom = etree.HTML(str(soup))
    companies = dom.xpath('//div[@class="wp-block-cover alignwide has-black-background-color has-background-dim is-position-center-center"]')

    company_data = []

    for company in companies:
        data = {}
        name = company.xpath(
            './/h3[@class="has-huge-font-size"]//descendant::span//text()')[0]
        links = dict(zip(company.xpath('.//a/text()'),
                     company.xpath('.//a/@href')))
        data["Name"] = name
        print(name)
        for link in links:
            data[link] = links[link]

        # Scrape linkedin data
        if (data["Linkedin"] != ''):
            li_data = linkedin_data(data["Linkedin"], li_driver)
            if li_data:
                data = {**data, **li_data}

        # Scrape capitaliq data
        capiq_driver.get('https://www.capitaliq.com/CIQDotNet/my/dashboard.aspx')
        found = find_company_page(name, capiq_driver)
        if found:
            print("company found")
            iq_data = scrape_iq_data(capiq_driver)
            data = {**data, **iq_data}
        else:
            print('company not found')

        company_data.append(data)
        print('\n')

    df = pd.DataFrame(company_data)
    df = df[[
        'Name',
        'Headquarters',
        'Founded',
        'Company size',
        'Revenue',
        'EBITDA',
        'Offices',
        'CEO',
        'CFO',
        'CTO',
        'Phone',
        'Solution',
        'Website',
        'Linkedin',
        'Crunchbase',
        'Facebook',
        'Twitter'
    ]]
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



def find_company_page(name, driver):
    search_bar = driver.find_element_by_name("SearchText")
    search_bar.send_keys(name)
    search_bar.send_keys(Keys.ENTER)

    # On company page
    if 'company' in driver.current_url:
        return True

    # Pick from suggestion
    elif 'Please see some suggested matches:' in driver.page_source:
        company_suggestions = driver.find_elements_by_xpath(
            '//table//*[contains(text(), "Company)")]')
        try:
            for i in range(min(5, len(company_suggestions))):
                href = company_suggestions[i]
                href.click()
                if 'company' in driver.current_url:
                    offices = driver.find_element_by_xpath(
                        '//a[contains(text(), "View All Office Addresses")]')
                    primary_office = offices.find_element_by_xpath(
                        './../../../../following-sibling::*').text.split('\n')[0]
                    if 'Australia' in primary_office:
                        return True
                    else:
                        driver.back()
                        company_suggestions = driver.find_elements_by_xpath(
                            '//table//*[contains(text(), "Company)")]')
                else:
                    driver.back()
                    company_suggestions = driver.find_elements_by_xpath('//table//*[contains(text(), "Company)")]')
            print(f'not found in first few links')
            return False
        except:
            print('need to debug')
            return False

    # Pick from search results
    else:
        company_suggestions = driver.find_elements_by_xpath('//table[@class="cTblListBody"]//*[@href]')
        try:
            for i in range(min(5, len(company_suggestions))):
                href = company_suggestions[i]
                href.click()
                if 'company' in driver.current_url:
                    offices = driver.find_element_by_xpath('//a[contains(text(), "View All Office Addresses")]')
                    primary_office = offices.find_element_by_xpath('./../../../../following-sibling::*').text.split('\n')[0]
                    if 'Australia' in primary_office:
                        return True
                    else:
                        driver.back()
                        company_suggestions = driver.find_elements_by_xpath('//table[@class="cTblListBody"]//*[@href]')
                else:
                    driver.back()
                    company_suggestions = driver.find_elements_by_xpath('//table[@class="cTblListBody"]//*[@href]')
            return False
        except:
            print('need to debug')
            return False



def scrape_iq_data(driver):
    data = {}

    # Scrape revenue
    try:
        revenue = driver.find_element_by_xpath(
            '//td//*[contains(text(), "Total Revenue")]').find_element_by_xpath('..//following-sibling::td').text
        revenue = float(revenue.replace(",", "").replace(
            "(", "").replace(")", "")) * (10**6)
        data['Revenue'] = revenue
        print(revenue)
    except:
        print("couldnt find revenue")

    # Scrape EBITDA
    try:
        ebitda = driver.find_element_by_xpath(
            '//td//*[contains(text(), "EBITDA")]').find_element_by_xpath('..//following-sibling::td').text
        ebitda = float(ebitda.replace(",", "").replace(
            "(", "").replace(")", "")) * (10**6)
        data['EBITDA'] = ebitda
        print(ebitda)
    except:
        print("couldnt find ebitda")

    # Scrape solution/value-chain
    try:
        solution = driver.find_element_by_xpath(
    '//table//*[contains(text(), "Primary Industry Classification")]//..//..//..//..//following-sibling::table').text.strip()
        data['Solution'] = solution
    except:
        print("couldn't find solution/value-chain")

    # Scrape execs
    d = pd.read_html(driver.page_source)
    for df in d[::-1]:
        df = df.astype(str)
        if 'Key Professionals View All' in df.values:
            try:
                execs = df.rename(columns=df.iloc[1]).drop(df.index[:2]).reset_index(drop=True).iloc[:, :2]
                execs['Title'] = execs['Title'].str.upper().str.replace(',', ' ')
                execs = execs.astype(str)
                try:
                    ceo = execs[execs.Title.apply(lambda x: any(identifier in x for identifier in [
                                                  'CEO', 'CHIEF EXECUTIVE OFFICER', "CHIEF EXEC. OFFICER"]))].Name.values[0]
                    data['CEO'] = ceo
                    print(ceo)
                except:
                    print("couldnt find ceo")
                try:
                    cfo = execs[execs.Title.apply(lambda x: any(identifier in x for identifier in [
                                                  'CFO', 'CHIEF FINANCIAL OFFICER']))].Name.values[0]
                    data['CFO'] = cfo
                    print(cfo)
                except:
                    print("couldnt find cfo")
                try:
                    cto = execs[execs.Title.apply(lambda x: any(identifier in x.replace(
                        'DIRECTOR', '') for identifier in ['CTO', 'CHIEF TECHNOLOGY OFFICER']))].Name.values[0]
                    data['CTO'] = cto
                    print(cto)
                except:
                    print("couldnt find cto")
            except:
                print("couldnt find exec table")
            break

    return data


main()
