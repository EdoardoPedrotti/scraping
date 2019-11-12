import logging
import re

import requests
import scrapy as scrapy
from bs4 import BeautifulSoup


class FarmDataSpider(scrapy.Spider):
    name = "farmadata"

    def start_requests(self):
        urls = ["https://placotrans.infarmed.pt/Publico/ListagemPublica.aspx"]
        for url in urls:
            self.log(f"scraping {url}")
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        filename = 'test.csv'
        placeholder = response.xpath('//*[@id="ctl00_ContentPlaceHolder1_gvDoacoesPublic"]').get()
        soup = BeautifulSoup(placeholder, 'html.parser')
        new_soup = soup.find_all('tr', re.compile('grid-row-style.*'))
        self.log(f"new soup {len(new_soup)}")
        for s in new_soup:
            all_tds = s.find_all('td')

            out = ",".join([re.sub(r"</?.{1,2}>", '', str(td)) for td in all_tds]) + "\n"
            self.log(out)
            with open(filename, 'a+') as f:
                f.write(out)


# def steal_data(url):
#     spidy = FarmDataSpider()
#     spidy.start_urls = [url]
#
#     spidy.start_requests()
#
#
#
#
# if __name__ == "__main__":
#     url = "https://placotrans.infarmed.pt/Publico/ListagemPublica.aspx"
#
#     steal_data(url)

