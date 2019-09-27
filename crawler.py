import re
import requests
import time
from bs4 import BeautifulSoup as Soup
import urllib
from urllib.parse import urlsplit


class crawler:
    def __init__(self):
        self.proxy="http://148.217.94.54:3128"

    #url parsing and formatting
    def entry(self):
        with open("states.csv","r") as states:
            for state in states:
                A_url=f"https://www.nigeriapropertycentre.com/for-rent/flats-apartments/{state.lower()}"
                url=urlsplit(A_url)
                print(url.geturl())
                yield url.geturl()


    def pagination(self,url):
        """generate possible url link for paginated pages """

        try:
            req=urllib.request.urlopen(url)
            pattern= re.compile(r"\d+([,]\d+)?$")
            page= Soup(req.read(), "html.parser")
            flats=page.find("span",{"class":"pagination-results"}).text
            results=pattern.search(flats)
            if "," in results.group(0):
                base,ten=results.group(0).split(",")
                flat=(base + ten)
            else:
                flat=results.group(0)
            url_range=round(int(flat)/20)
            print(url_range)
            # check that there is more than one page for this intended resource
            if url_range>1:
                for i in range(1,url_range):
                     #url pattern hunting to navigate pages using string format on the url
                    new_url=str((i+1)*10)
            else:
                pass
        except Exception as e:
            pass


    #a helper function to help extract links for the details of each building
    def extract_links(self, url):
        req=requests.get(url)
        page=Soup(req.content, "html.parser")
        links=page.find_all("div",class_= "wp-block-body")
        for link in links:
            hrefs=link.select("a")
            for href in hrefs:
                if href.text=="More details":
                    link = f"https://www.nigeriapropertycentre.com{href['href']}"
                    yield link



    def extract_details(self, urls):
        req=requests.get(urls)
        page=Soup(req.content,"html.parser")
        building_address= page.find("address").text
        pattern=re.compile(r'(\w+$)')
        state=pattern.search(building_address)
        building_price=page.select(".price")
        for price in building_price:
            if price.get('itemprop')=="price" and price['content']!=None:
                price=int(float(price['content']))
        contact_info = page.select("input[type=hidden]")
        for info in contact_info:
            if info.get('id')=="fullPhoneNumbers":
                contact=info["value"]
        return building_address, price, state.group(0), contact





if __name__ == '__main__':
    print("execution started")
    crawler=crawler()
    entry=crawler.entry()
    print()
    for _ in range(35):
        crawler.pagination(next(entry))
    print()
    # links=crawler.extract_links(url)
    # for _ in range(20):
    #     print(crawler.extract_details(next(links)))
