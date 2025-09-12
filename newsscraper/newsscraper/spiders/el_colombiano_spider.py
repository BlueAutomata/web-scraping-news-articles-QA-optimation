import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
import os


class ElColombianoSpiderSpider(scrapy.Spider):
    name = "el_colombiano_spider"
    allowed_domains = ["www.elcolombiano.com"]
    start_urls = ["https://www.elcolombiano.com"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", 'div.Card-ImagePosition')
                    ],
                    "category": os.path.basename(urlparse(url).path.rstrip('/'))
                }
            )

    def parse(self, response):
        pass
