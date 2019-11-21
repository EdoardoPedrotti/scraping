import re
from time import sleep

import scrapy as scrapy
from bs4 import BeautifulSoup
from scrapy_selenium import SeleniumRequest
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

comma_float = re.compile("\s*\d+,\d+")


class FarmDataSpider(scrapy.Spider):
    name = "farmadata"
    page = 1
    urls = ["https://placotrans.infarmed.pt/Publico/ListagemPublica.aspx"]

    def start_requests(self):
        for url in self.urls:
            self.log(f"scraping {url}")
            yield SeleniumRequest(url=url, callback=self.parse, screenshot=True)

    def parse(self, response):
        filename = "test.csv"
        container_xpath = '//*[@id="ctl00_ContentPlaceHolder1_gvDoacoesPublic"]'
        placeholder = response.xpath(
            container_xpath
        ).get()
        soup = BeautifulSoup(placeholder, "html.parser")
        new_soup = soup.find_all("tr", re.compile("grid-row-style.*"))
        for s in new_soup:
            all_tds = s.find_all("td")

            out = ",".join([self.extract_info(td) for td in all_tds]) + "\n"
            with open(filename, "a+") as f:
                f.write(out)
        while True:
            try:
                self.page += 1
                self.log(f"page {self.page}")
                driver = response.request.meta['driver']
                # driver.find_element_by_xpath(f"//*[text() = {self.page}]").click()
                sleep(3)
                WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, f"//*[text() = {self.page}]"))).click()
                container = driver.find_element_by_xpath(container_xpath)
                soup = BeautifulSoup(container.get_attribute('innerHTML'), "html.parser")
                new_soup = soup.find_all("tr", re.compile("grid-row-style.*"))
                self.log(f"new soup {len(new_soup)}")
                for s in new_soup:
                    all_tds = s.find_all("td")

                    out = ",".join([self.extract_info(td) for td in all_tds]) + "\n"
                    with open(filename, "a+") as f:
                        f.write(out)
            except NoSuchElementException as e:
                self.log(e)
                break

    def dump_screenshot(self, response):
        with open('image.png', 'wb') as image_file:
            image_file.write(response.meta['screenshot'])

    def extract_info(self, td):
        text = re.sub(r'</?.{1,2}.*>', "", str(td))
        text = re.sub(r"\s{2}", "", text)
        value = text
        if comma_float.match(text):
            value = re.sub(r"\s+", "", text).replace(",", ".")
        return value
