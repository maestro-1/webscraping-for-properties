import re
import requests
import time
import urllib
import concurrent.futures
from bs4 import BeautifulSoup as Soup
from urllib.parse import urlsplit


class crawler:
    """ To crawl a website and extract information from all the sites pages.
    The init method holds an attribute should you chose to proxy the server at any point during use
    Note there are two extract functions this is due to capatibility reasons as interchanging them may cause the
    crawler to break or act in an usual manner. The paginated pages of the sites have been handled using byte like urls
    while other url were handled in string form"""

    def __init__(self):
        self.proxy="http://148.217.94.54:3128"

    #url parsing and formatting
    def entry(self):
        with open("states.csv","r") as states:
            for state in states:
                A_url=f"https://www.nigeriapropertycentre.com/for-rent/flats-apartments/{state.lower()}"
                url=urlsplit(A_url)
                yield url.geturl()


    def pagination(self,url):
        """generate possible url  for paginated pages """

        try:
            req=urllib.request.urlopen(url)
            pattern= re.compile(r"\d+([,]\d+)?$")
            state=url.split('/')[5]
            page= Soup(req.read(), "html.parser")
            flats=page.find("span",{"class":"pagination-results"}).text
            results=pattern.search(flats)
            if "," in results.group(0):
                base,ten=results.group(0).split(",")
                flat=(base + ten)
            else:
                flat=results.group(0)
            url_range=round(int(flat)/20)
            # check that there is more than one page for this intended resource
            if url_range>1:
                # print(state)
                new_url=[str((i+1)) for i in range(1,url_range)] + [state]
                 #url pattern hunting to navigate pages using string format on the url
                yield new_url

            else:
                pass
        except Exception as e:
            pass


    def page_url(self,*args):
        for arg in args:
            payloads=arg
            payload=payloads[:-1]
            state=payloads[-1]
            for value in payload:
                url=f"https://www.nigeriapropertycentre.com/for-rent/flats-apartments/{state.strip()}?page={value}"
                yield url

    #a helper function to help extract links for the details of each building
    def extract_links1(self, url):
        url=url.encode("utf-8")
        req=requests.get(url)
        page=Soup(req.content, "html.parser")
        links=page.find_all("div",class_= "wp-block-body")
        for link in links:
            hrefs=link.select("a")
            for href in hrefs:
                if href.text=="More details":
                    link = f"https://www.nigeriapropertycentre.com{href['href']}"
                    yield link


    def extract_links2(self, url):
        req=urllib.request.urlopen(url)
        page=Soup(req.read(), "html.parser")
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
        print(building_address, price, state.group(0), contact)
        return building_address, price, state.group(0), contact


    def execution1(self):
        entries=self.entry()
        for entry in entries:
            try:
                pages=self.pagination(entry)
                for page in pages:
                    urls=self.page_url(page)
                    for url in urls:
                        # res=requests.get(url)
                        links=self.extract_links1(url)
                        for _ in range(20):
                            try:
                                print(self.extract_details(next(links)))
                            except Exception as e:
                                pass
            except Exception as e:
                pass


    def execution2(self):
        entries=self.entry()
        for entry in entries:
            try:
                links=crawler.extract_links2(entry)
                for _ in range(20):
                        crawler.extract_details(next(links))
            except Exception as e:
                pass



if __name__ == '__main__':
    print("execution started")
    crawler=crawler()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(crawler.execution2)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.submit(crawler.execution1)
