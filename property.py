import csv
import logging
import os
import re
import requests
import sqlite3
import time
from bs4 import BeautifulSoup as Soup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait



conn=sqlite3.connect("property.db")
c=conn.cursor()


class NaijaProperties:
    def __init__(self):
        self.options=Options()
        self.options.headless=True
        self.options.add_argument("ignore-certificate-errors")
        self.options.add_argument("--proxy-server=http://148.217.94.54:3128")
        self.driver=webdriver.Chrome(options=self.options)
        self.action= ActionChains(self.driver)
        self.wait=WebDriverWait(self.driver,50)
        self.parent_tab= self.driver.window_handles[0]
        self.url=self.driver.current_url


    # create a csv file to later loop through as a shortcut: helper function
    def states(self):
        create_DB()
        try:
            self.driver.get("http://www.umunna.org/nigeria_state.html")
            with open("states.csv", "w") as states:
                parentTab=self.driver.find_elements_by_xpath('/html/body/div[3]/div/div[3]/table/tbody/tr/td[1]/h2/font')
                for i in parentTab:
                    states.write(i.text)
        except Exception as e:
            print(logging.error(e))




    # navigating to the required webpage location
    def setup(self,http_address,text_to_send):
        self.driver.get(http_address)
        self.popup()
        self.driver.find_element_by_xpath('//*[@id="li-cid-for-rent"]/a/label').click()
        self.driver.find_element_by_id('tid').send_keys(text_to_send)

        # loop through csv file created and extract names from it into loop for process
        with open("states.csv","r") as states:
            for line in csv.reader(states):
                stat=str(line)
                state=stat[2:-2].lower().capitalize()

                    # check if in intended webpage location and respond appropriately
                if self.driver.current_url != text_to_send:
                    self.interact(http_address)
                else:
                    self.popup()
                    self.driver.find_element_by_xpath('//*[@id="li-cid-for-rent"]/a/label').click()
                    self.driver.find_element_by_id('tid').send_keys("flats")
                text=self.driver.find_element_by_id("propertyLocation")
                text.clear()
                text.send_keys(state)
                time.sleep(2)
                text.send_keys(Keys.ENTER)

                detail=self.details("More details","wp-block property list","wp-block hero light")
                if detail != None:
                    self.next_page(state)
                else:
                    continue


    # helper function for navigation
    def interact(self,http_address):
        self.driver.execute_script(f"window.location.replace('{http_address}');")
        self.driver.find_element_by_xpath('//*[@id="li-cid-for-rent"]/a/label').click()
        self.driver.find_element_by_id('tid').send_keys("flats")



    # function for locating the links on the page and extracting the links for redirecting
    def details(self,link_text,resouces_class,no_resource_class):
        detail=self.driver.find_elements_by_xpath("//*")
        for i,ch in enumerate(detail):
            info = detail[i].get_attribute("class")

            # target properties are present in pages with this class, respond appropriately
            if info==resouces_class:
                links=self.driver.find_elements_by_link_text(link_text)

                # loop through the links, open pages and extract info then close pages
                for link in links:
                    href=link.get_attribute("href")
                    self.driver.execute_script(f"window.open('{href}');")
                    self.extract()
                break

            # target properties are not present as far as this class is involved
            if info==no_resource_class:
                self.driver.execute_script("history.go(-1);")
                self.popup()
                return None
        return "properties available"



    # helper function to help extraction
    def extract(self):
        child_tab=self.driver.window_handles[1]
        self.driver.switch_to.window(child_tab)

        #copy intended texts from page after it appears using static scraping
        self.extraction_process()

        #close tabs
        self.driver.close()
        self.driver.switch_to.window(self.parent_tab)


    # helper function for the final extraction
    def extraction_process(self):
        url=self.driver.current_url
        req=requests.get(url)
        page=Soup(req.text,"html.parser")
        building_address= self.driver.find_element_by_tag_name("address").text
        pattern=re.compile(r'(\w+$)')
        state=pattern.search(building_address)
        building_price=page.select(".price")
        for price in building_price:
            if price.get('itemprop')=="price":
                if price['content']!=None:
                    contact_info= page.select("input[type=hidden]")
                    for info in contact_info:
                        if info.get('id')=="fullPhoneNumbers":
                            print(info["value"])
                            insert_rent([building_address],float(price['content']), state.group(0),[info['value']])
                            return None



    # navigating to the next page if there is more than one page
    def next_page(self,state_looking_through):
        try:
            # return to parent window
            self.driver.switch_to.window(self.parent_tab)

            pattern=re.compile(r"\d+([,]\d+)?$")

            # obtain the number of available flats there are in the region using static scraping(BeautifulSoup)
            # and divide by 20 to get the number of pages
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

                # check that there is more than one page for this intended resource
                if url_range>1:
                    for i in range(1,url_range):

                         #url pattern hunting to navigate pages using string format on the url
                        new_url=str((i+1)*10)
                        page= f"https://www.nigeriapropertycentre.com/for-rent/flats-apartments/{state_looking_through.lower()}/results" + f"?limitstart={new_url}&q={state_looking_through.lower()}+for-rent+flats-apartments&selectedLoc="  #urls for extended pages
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
        print("program has started execution")
        if os.path.exists("states.csv"):
            pass
        else:
            self.states()
        self.setup("https://www.nigeriapropertycentre.com/","flats")
        self.teardown()


def create_DB():
    with conn:
        c.execute("""CREATE TABLE rent(
        location text,
        price integer,
        state text,
        contact text
        )
        """)

def insert_rent(*args):
    arg1,arg2,arg3,arg4=args
    location=" ".join(arg1)
    price=arg2
    state=arg3
    contact=" ".join(arg4)
    with conn:
        c.execute("insert into rent values (:location, :price, :state, :contact)", {'location': location, 'price':price, 'state':state, 'contact':contact})

def search():
    with conn:
        c.execute("SELECT * FROM rent")
        print(c.fetchall())


if __name__ == '__main__':
    naija=NaijaProperties()
    naija.execute()
