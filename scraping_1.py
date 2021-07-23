import time
import sys
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import *
from selenium.webdriver.support.ui import *
import re
import os
import requests
import pandas as pd
import math
from datetime import datetime
import random

class zillow_scraper:
    
    FirstLine = True
    #Excel row value
    Rows = 0
    ## Defining options for chrome browser
    options = webdriver.ChromeOptions()
    #ssl certificate error ignore
    options.add_argument("--ignore-certificate-errors")
    #Adding proxy
    #options.add_argument('--proxy-server=%s' % PROXY')


    browser = webdriver.Chrome(executable_path = "chromedriver",options = options)

    #MainUrl = 'https://www.zillow.com/homedetails/5239-E-Abbeyfield-St-Long-Beach-CA-90815/21203457_zpid/'

    #Excel File Name
    FileName = "ScrapedData"+str(random.randint(1,9789))+"-"+str(datetime.today().date())+".xlsx"
    #Defining Excel Writer
    ExcelFile = pd.ExcelWriter(FileName)


    def zillow_data(self,url):
        self.browser.get(url)
        #extracting phone number and owner name
        try:
            phone_ownername = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//p[@data-testid='attribution-owner']"))).text
            #replacing spaces with - so we can use phone no regex properly eg: Property-Owner-(949)-294-2625
            phone_ownername = phone_ownername.replace("-" , " ")
            phone_no = re.compile(r'\([0-9]{3}\)\s[0-9]{3}\s[0-9]{4}$').findall(phone_ownername)[0]
            #striping phone no from Property-Owner-(949)-294-2625 so we can get our ownername
            ownername = phone_ownername.strip(phone_no)
        #if there is indexerror that means phone no number is not present only owner name present
        except IndexError:
            phone_ownername = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//p[@data-testid='attribution-owner']"))).text
            phone_no = ""
            ownername = phone_ownername
        #if non of them are present
        except TimeoutException:
            phone_no = ""
            ownername = ""


        #extracting address as in whole eg 5239 E Abbeyfield St, Long Beach, CA 90815
        #then splitting address by comma so we will address like this ['Abbeyfield St','Long Beach','CA 90815']
        #first index will be street second index will be city and the third will be both state and zip code
        adress = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class ='Text-c11n-8-37-1__aiai24-0 gCmWjL ds-price-change-address-row']//h1[@id='ds-chip-property-address']"))).text
        adress = adress.split(",")
        street = adress[0]
        city = adress[1]
        #for state and zip code we will strip space from corners and split by space so we will get both state and zip on differnt index
        sc = adress[-1].rstrip().lstrip().split(" ")
        state = sc[0]
        zip1 = sc[-1]
        buy_zestimate = ""
        rental_zestimate = ""

        #description
        try:
            description = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//div[@class='ds-overview-section']//div"))).get_attribute('innerHTML')

        #print(description)
        except TimeoutException:

            description = ""

        #Main Price
        try:    
            price = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//span[@class='Text-c11n-8-37-1__aiai24-0 sc-oTpqt jVKtyn']"))).text
        except TimeoutException: 
            price = ""
        timeonzillow = ""

        # for time on zillow we get 3 divs with same structure : Time on Zillow 3 days | Views 464 | Saves 9 : we will iterate them and if any of them has Time on Zillow present in
        try:
            time_onzillow = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//div[@class='sc-oVcRo jroYxY']")))
            for time in time_onzillow: 
                if "Time on Zillow" in time.text:
                    timeonzillow = time.text.replace("Time on Zillow" , "")
        except TimeoutException:
            pass
        ptype= ""

        #we will do same thing as above for Type too as we did for Time on Zillow
        try:
            type_zillow = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.XPATH,"//ul[@class='ds-home-fact-list']//li[@class='ds-home-fact-list-item']")))
            for type_on in type_zillow:
                if "Type:" in type_on.text:
                    ptype = type_on.text.split("Type:")[-1]
        except TimeoutException:
            pass

        #for zestimage and rent zestimage both html structure is same so we will find both together and will iterate if Rent Zestimate text is present that means is Rest Zestimate
        try:
            zestimate = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.XPATH,"//div[@class='Flex-c11n-8-37-1__n94bjd-0 hScDTe']")))
            for zest in zestimate:
                if "Rent Zestimate" in zest.text:
                    rental_zestimate = zest.text.replace("Rent Zestimate®", "")
                elif "Zestimate" in zest.text:
                    buy_zestimate = zest.text.replace("Zestimate®", "")
        except TimeoutException:
            pass 
        #print(buy_zestimate)
        #print(rental_zestimate)

        #Saving the data to Excel
        self.WriteDataToExcel(url,phone_no,street,city,state,zip1,ownername,description,price,timeonzillow,ptype,buy_zestimate,rental_zestimate)


    def WriteDataToExcel(self,pageurl,phone,address,city,state,zipcode,ownern,desc,price,toz,ptype,zestimate,rentzestimate):
        Data_Dict = {
            'URL' : pageurl,
            'Phone Number' : phone,
            'Address' : address,
            'City' : city,
            'State' : state,
            'Zip' : zipcode,
            'Owner Name' : ownern,
            'Description' : desc,
            'Price' : price,
            'Time on Zillow' : toz,
            'Type' : ptype,
            'Zestimate' : zestimate,
            'Rent Zestimate' : rentzestimate
        }

        if self.FirstLine == True:
            df = pd.DataFrame([Data_Dict])
            df.to_excel(self.ExcelFile,index=False,sheet_name='Data',header=True,startrow=self.Rows)
            self.Rows = self.ExcelFile.sheets['Data'].max_row
            self.FirstLine = False
        else:
            df = pd.DataFrame([Data_Dict])
            df.to_excel(self.ExcelFile,index=False,sheet_name='Data',header=False,startrow=self.Rows)
            self.Rows = self.ExcelFile.sheets['Data'].max_row

        self.ExcelFile.save()

    def getting_urls(self,url):
        #urls list
        PropertyURLS = []
        print("FileName : "+self.FileName)
        self.browser.get(url)

        #iterate till there is no next page
        while True:
            time.sleep(2)
            #Click on other listing button
            element_1 = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//button[@alt='Switch to Other listings']")))
            self.browser.execute_script("arguments[0].click();", element_1)
            #Iterate loop 9 times and press PAGEDOWN key on each iterate to get the bottom of the page we could us END button but it will not load the all the properties
            for i in range(9):
                element_1.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.5)

            time.sleep(2)
            #Getting url for all the article present in the page and then storing them in to  PropertyURLS list
            get_article = WebDriverWait(self.browser, 10).until(EC.presence_of_all_elements_located((By.XPATH, "//article[@class='list-card list-card-additional-attribution list-card_not-saved']//div[@class='list-card-info']//a[@class='list-card-link list-card-link-top-margin']")))
            for article in get_article:
                PropertyURLS.append(article.get_attribute("href"))
            #We are pressing ENTER key on next button and then we are checking if disabled is the mentioned in the a tag if it's mention that means its last page    
            next_button = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, "//ul[@class='PaginationList-c11n-8-37-0__sc-14rlw6v-0 hmdLoo']//li[@class='PaginationJumpItem-c11n-8-37-0__sc-18wdg2l-0 eGOQHk']//a[@title='Next page']")))
            if next_button.get_attribute('disabled') == "true":
                break
            next_button.send_keys(Keys.ENTER)

        return PropertyURLS

    def connector(self):
        UserInput = str(input("Enter Url: "))
        print("Scraping data for url : "+str(UserInput))
        #Calling gettingurl function it will scrape all the properties url from search result
        urls = self.getting_urls(UserInput)
        #log
        print("Total Properties found : ",len(urls))
        i = 0
        for url in urls:
            i += 1
            print("Property Scraping : "+url)
            #zillow data function will scrape mandatory fields and save it to excel
            self.zillow_data(url)
            #log
            print("Property Scraped : "+str(i)+" out of "+str(len(urls))+" remaining urls : "+str(len(urls) - i))

a=zillow_scraper()
a.connector()
#a.zillow_data("https://www.zillow.com/homedetails/4152-Lake-Harbor-Ln-Westlake-Village-CA-91361/19891427_zpid/")




  

