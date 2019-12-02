import logging
import re
from time import sleep

import scrapy as scrapy
from bs4 import BeautifulSoup
from scrapy_selenium import SeleniumRequest
from selenium.common.exceptions import NoSuchElementException
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
        filename = "dump.csv"
        container_xpath = '//*[@id="ctl00_ContentPlaceHolder1_gvDoacoesPublic"]'
        loading_div = '//*[@id="ctl00_updateProgress"]/div'
        driver = response.request.meta["driver"]
        driver.set_window_size(2480, 1344)
        driver.find_element_by_xpath(
            '//*[@id="ctl00_ContentPlaceHolder1_1_2018"]'
        ).click()
        sleep(3)
        while True:
            try:
                self.log(f"page {self.page}", level=logging.INFO)
                # driver.find_element_by_xpath(f"//*[text() = {self.page}]").click()
                # next.click()

                soup = BeautifulSoup(
                    driver.find_element_by_xpath(container_xpath).get_attribute("innerHTML"), "html.parser"
                )
                new_soup = soup.find_all("tr", re.compile("grid-row-style.*"))
                for s in new_soup:
                    all_tds = s.find_all("td")

                    out = (
                        ",".join([self.extract_info(td) for td in all_tds])
                        + f",{self.page}\n"
                    )
                    with open(filename, "a+") as f:
                        f.write(out)
                driver.find_element_by_xpath("/html").screenshot(
                    f"lastpage.png"
                )
                self.page += 1
                if self.page == 21:
                    self.log(
                        f"click on more button on page {self.page}", level=logging.INFO
                    )
                    wait = WebDriverWait(driver, 30)
                    element = wait.until(
                        EC.invisibility_of_element((By.XPATH, loading_div))
                    )
                    next = driver.find_element_by_xpath(
                        '//*[@id="ctl00_ContentPlaceHolder1_pageCounterDoacoes_ctl21_Pager"]'
                    )
                    next.click()
                    driver.find_element_by_xpath(
                        '//*[@id="tabs-1"]/div[2]/div[2]'
                    ).screenshot("nav_bar.png")
                    sleep(8)
                else:
                    self.log(f"next page {self.page}", level=logging.INFO)
                    wait = WebDriverWait(driver, 30)
                    element = wait.until(
                        EC.invisibility_of_element((By.XPATH, loading_div))
                    )
                    next = WebDriverWait(driver, 30).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, f"//*[text() = {self.page}]")
                        )
                    )
                    next.click()
                    sleep(8)
            except NoSuchElementException as e:
                driver.find_element_by_xpath("/html").screenshot(
                    f"maybe-last-page-{self.page}.png"
                )
                self.log(e)
                break

    def dump_screenshot(self, response, page):
        with open(f"page-{page}.png", "wb") as image_file:
            image_file.write(response.meta["screenshot"])

    def extract_info(self, td):
        # td = td.replace("style = bold")
        # text = re.sub(r'</?.{1,2}.*>', "", str(td))
        #
        # text = re.sub(r"\s{2}", "", text)
        text = td.text
        value = text
        if comma_float.match(text):
            value = re.sub(r"\s+", "", text).replace(",", ".")
        return value
