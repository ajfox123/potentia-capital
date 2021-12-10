import pandas as pd
from lxml import etree
import requests
import json
from bs4 import BeautifulSoup as bs
from selenium import webdriver
import chromedriver_binary
import time



def main():
    driver = webdriver.Chrome()
    driver.get("https://www.linkedin.com/")

    username_box = driver.find_element_by_id("session_key")
    #username = input("LinkedIN Username: ")
    username = 'ajfox123@gmail.com'
    username_box.send_keys(username)

    password_box = driver.find_element_by_id("session_password")
    #password = input("LinkedIN Password: ")
    password = 'Loopytro0L!'
    password_box.send_keys(password)

    login_button = driver.find_element_by_class_name("sign-in-form__submit-button")
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
            li_data = linkedin_data(data["Linkedin"], driver)
            if li_data:
                data = {**data, **li_data}
        
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
    
    # Get executive information
    ceo_url = url + 'people/?keywords=chief%20executive%20officer'
    driver.get(ceo_url)
    driver.implicitly_wait(1)
    try:
        ceo_card = driver.find_element_by_xpath('.//*[@class="org-people-profile-card__profile-title t-black lt-line-clamp lt-line-clamp--single-line ember-view"]')
        ceo_name = ceo_card.text
        data["CEO"] = ceo_name
        print(ceo_name)
    except:
        try:
            ceo_url = url + 'people/?keywords=ceo'
            driver.get(ceo_url)
            driver.implicitly_wait(1)
            ceo_card = driver.find_element_by_xpath('.//*[@class="artdeco-entity-lockup__content ember-view"]')
            ceo_title = ceo_card.find_element_by_xpath('.//*[@class="artdeco-entity-lockup__subtitle ember-view"]')
            if 'CEO' in ceo_title.text:
                ceo_name = ceo_card.text
                data["CEO"] = ceo_name
                print(ceo_name)
        except:
            print('ceo not found')
        
    return data




main()