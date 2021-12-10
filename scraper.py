from selenium import webdriver
import chromedriver_binary
import pandas as pd
from tabulate import tabulate
from lxml import html
import json
from bs4 import BeautifulSoup

def main():
    # Simulates a user to bypass authentication
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
    
    # Search for each company and extract info
    d = []
    
    companies = {
        "Aconex": [
            "https://www.linkedin.com/company/aconex/about/",
            "https://www.crunchbase.com/organization/aconex"
        ],
        "Align Construction Technologies": [
            "https://www.linkedin.com/company/alignrobotics/",
            "https://www.crunchbase.com/organization/align-construction-technologies"
        ],
        "Buildxact": [
            "https://www.linkedin.com/company/buildxact/about/"
        ],
        "CIM": [
            "https://www.linkedin.com/company/cimsoftware/about/"
        ],
        "EstimateOne": [
            "https://www.linkedin.com/company/estimateone-pty-ltd/about/"
        ],
        "Fastbrick Robotics": [
            
        ],
        "SiteHive": [
            "https://www.linkedin.com/company/sitehive/about/"
        ]
    }
    #add stock symbol
    for company in companies:
        company_data = {"Name": company}
        company_data = {**company_data, **linkedin_data(companies[company][0], driver)}
        if len(companies[company] > 1):
            a = crunchbase_data(companies[company][1])
        d.append(company_data)
        
    df = pd.DataFrame(d)
    print(tabulate(df, headers='keys', tablefmt='psql'))
    df.to_csv("company_data.csv", index=False)



def linkedin_data(linkedin_url, driver):
    data = {}
    
    driver.get(linkedin_url)

    els = driver.find_elements_by_xpath("//dt[@class='mb1 text-heading-small']")
    
    for i in els:
        el_info = i.find_element_by_xpath('./following-sibling::dd[1]')
        data[i.text] = el_info.text
    
    locations = driver.find_element_by_xpath("//h3[@class='t-20 t-bold']").text
    locations = locations[locations.index('(')+1:locations.index(')')]
    data["Offices"] = locations
    return data



def crunchbase_data(crunchbase_url, driver):
    data = {}
    
    driver.get(crunchbase_url)

    els = driver.find_elements_by_xpath("//dt[@class='mb1 text-heading-small']")
    
    for i in els:
        el_info = i.find_element_by_xpath('./following-sibling::dd[1]')
        data[i.text] = el_info.text
    
    locations = driver.find_element_by_xpath("//h3[@class='t-20 t-bold']").text
    locations = locations[locations.index('(')+1:locations.index(')')]
    data["Offices"] = locations
    return data
main()