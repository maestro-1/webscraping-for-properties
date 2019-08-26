import csv
import logging
import os
import re
import requests
import sqlite3
import time
from bs4 import BeautifulSoup as Soup
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.proxy import Proxy,ProxyType
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait



conn=sqlite3.connect("property.db")
c=conn.cursor()


class NaijaProperties:
    def __init__(self):
        self.prox=Proxy()
        self.prox.proxy_type=ProxyType.MANUAL
        self.prox.http_proxy= "149.215.113.110:70"
        self.prox.socks_proxy= "149.215.113.110:70"
        self.prox.ssl_proxy= "149.215.113.110:70"
        self.options=webdriver.ChromeOptions()
        self.options.Proxy=self.prox
        self.options.add_argument("ignore-certificate-errors")
        self.driver=webdriver.Chrome(options=self.options)
        self.action= ActionChains(self.driver)
        self.wait=WebDriverWait(self.driver,50)
        self.parent_tab= self.driver.window_handles[0]
        self.url=self.driver.current_url


    # create a csv file to later loop through as a shortcut: helper function
    def states(self):
        try:
            self.driver.get("http://www.umunna.org/nigeria_state.html")
            with open("states.csv", "w") as states:
                parentTab=self.driver.find_elements_by_xpath('//*[@id="main"]/table/tbody/tr/td[1]/h2')
                for i in parentTab:
                    states.write(i.text)
        except Exception as e:
            print(logging.error(e))




    # navigating to the required webpage location
    def setup(self):
            self.driver.get("https://www.nigeriapropertycentre.com/")
            self.popup()
            self.driver.find_element_by_xpath('//*[@id="li-cid-for-rent"]/a/label').click()
            self.driver.find_element_by_id('tid').send_keys("flats")
            # database=create_DB()

            # loop through csv file created and extract names from it into loop for process
            with open("states.csv","r") as states:
                for line in csv.reader(states):
                    stat=str(line)
                    state=stat[2:-2].lower().capitalize()

                        # check if in intended webpage location and respond appropriately
                    if self.driver.current_url != "https://www.nigeriapropertycentre.com/":
                        self.interact()
                    else:
                        self.popup()
                        self.driver.find_element_by_xpath('//*[@id="li-cid-for-rent"]/a/label').click()
                        self.driver.find_element_by_id('tid').send_keys("flats")
                    text=self.driver.find_element_by_id("propertyLocation")
                    text.clear()
                    text.send_keys(state)
                    time.sleep(2)
                    text.send_keys(Keys.ENTER)

                    detail=self.details()
                    if detail == "properties available":
                        print("running")
                        self.next_page(state)
                    else:
                        continue


    # helper function for navigation
    def interact(self):
        self.driver.execute_script("window.location.replace('https://www.nigeriapropertycentre.com/');")
        self.driver.find_element_by_xpath('//*[@id="li-cid-for-rent"]/a/label').click()
        self.driver.find_element_by_id('tid').send_keys("flats")



    # function for locating the links on the page and extracting the links for redirecting
    def details(self):
        detail=self.driver.find_elements_by_xpath("//*")
        for i,ch in enumerate(detail):
            info = detail[i].get_attribute("class")

            # target properties are present in pages with this class, respond appropriately
            if info=="wp-block property list":
                links=self.driver.find_elements_by_link_text("More details")
                url_links=list(links)

                # loop through the links, open pages and extract info then close pages
                for link in links:
                    href=link.get_attribute("href")
                    self.driver.execute_script(f"window.open('{href}');")
                    self.extract()
                break

            # target properties are not present as far as this class is involved
            if info=="wp-block hero light":
                self.driver.execute_script("history.go(-1);")
                self.popup()
                break
                return None

        return "properties available"



    # helper fucntion to help extraction
    def extract(self):
        child_tab=self.driver.window_handles[1]
        self.driver.switch_to.window(child_tab)

        # find and click number button via javascript execution
        self.driver.execute_script("showPhoneNumbers()")
        

        #copy intended texts from page after it appears using static scraping
        rent_data=self.extraction_process()
        # insert_rent(rent_data)

        #close tabs
        self.driver.close()
        self.driver.switch_to.window(self.parent_tab)


    # helper function for the final extraction
    def extraction_process(self):
        url=self.driver.current_url
        print(url)
        req=requests.get(url)
        page=Soup(req.text,"html.parser")
        building_address= self.driver.find_element_by_tag_name("address")
        building_price= page.find("span",{"class":"price"})
        building_details= page.find("table",{"class":"table table-bordered table-striped"})
        # contact_info= page.find("div",{"class":"text-center voffset-20"})
        contact_info= page.find("span",{"data-type":"phoneNumber"})
        print(contact_info)
        # return (building_address,building_price,building_details,contact_info)


    # navigating to the next page if there is more than one page
    def next_page(self,state_looking_through):
        try:
            # return to parent window
            self.driver.switch_to.window(self.parent_tab)

            pattern=re.compile(r"\d+([,]\d+)?$")

            # obtain the number of available flats there are in the region using static scraping(BeautifulSoup) and divide by 20 to get the number of pages
            url=self.driver.current_url
            req=requests.get(url)
            s_page=Soup(req.text, "html.parser")
            flats=s_page.find("span",{"class":"pagination-results"}).text
            number_of_flats=pattern.finditer(flats)
            for flat in number_of_flats:
                fla=str(flat.group(0))
                if "," in fla:
                    base,ten=fla.split(",")
                    flat=(base + ten)
                else:
                    flat=flat.group(0)
                url_range=round(int(flat)/20)
                print(url_range)

                # check that there is more than one page for this intended resource
                if url_range>1:
                    for i in range(1,url_range):

                         #url pattern hunting to navigate pages using string format on the url
                        new_url=str((i+1)*10)
                        page= "https://www.nigeriapropertycentre.com/for-rent/flats-apartments/" + state_looking_through.lower() + "/results" + f"?limitstart={new_url}&q=" +  state_looking_through.lower() + "+for-rent+flats-apartments&selectedLoc="  #urls for extended pages
                        print(self.driver.current_url)
                        print(page)
                        self.driver.execute_script("window.location.replace('{}')".format(page))
                        self.details()
                else:
                    pass
                break
        except Exception as e:
            pass


    # deal with all unwanted popups
    def popup(self):
        try:
            alert=self.driver.switch_to.alert()
            alert.dismiss()
        except Exception as e:
            pass



    # destroy session
    def teardown(self):
        self.driver.quit()



    # run program execution
    def execute(self):
        # if os.path.exists(r"Scripts/webscrap/states.csv")==False:
        #     self.states()
        # else:
        #     pass
        self.setup()
        self.teardown()


def create_DB():
    with conn:
        c.execute("""CREATE TABLE rent(
        location text,
        price integer,
        description text,
        contact integer
        )
        """)

# def insert_rent(*args):
    # (arg1,arg2,arg3,arg4)=args
    # print(arg1,arg2,arg3,arg4)
    # with conn:
        # c.execute("INSERT INT0 rent VALUES (:location, :price, :description, :contact)",{'location': arg1, 'price': arg2, 'description': arg3, 'contact':arg4})


if __name__ == '__main__':
    naija=NaijaProperties()
    naija.execute()
