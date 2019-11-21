import logging
import re

import requests
import scrapy as scrapy
from bs4 import BeautifulSoup

comma_float = re.compile("\s*\d+,\d+")

class FarmDataSpider(scrapy.Spider):
    name = "farmadata"
    page = 1

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

            out = ",".join([self.extract_info(td) for td in all_tds]) + "\n"
            with open(filename, 'a+') as f:
                f.write(out)

        link_table = response.xpath('//*[@id="tabs-1"]/div[2]/div[2]/table').get()
        link_soup = BeautifulSoup(link_table, 'html.parser')
        all_links = link_soup.find_all('a')
        for l in all_links:
            if int(l.next) == self.page +1:
                self.log(f"going to page {l.next}")
                self.page += 1
                next_page = response.urljoin(l.get('href'))
                yield scrapy.Request(next_page, callback=self.parse)
        self.log(all_links)



    def extract_info(self, td):
        text = re.sub(r"</?.{1,2}>", '', str(td))
        text = re.sub(r"\s{2}","", text)
        value = text
        if comma_float.match(text):
            value = re.sub(r"\s+", "", text).replace(",", ".")
        return value

