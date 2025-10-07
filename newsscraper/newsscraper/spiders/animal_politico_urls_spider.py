import json
import os
import scrapy
from urllib.parse import urlparse
from datetime import datetime
from newsscraper.items import NewsItem
from scrapy_playwright.page import PageMethod

class AnimalPoliticoUrlsSpiderSpider(scrapy.Spider):
    name = "animal_politico_urls_spider"
    allowed_domains = ["animalpolitico.com"]

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "CONCURRENT_REQUESTS": 10,
        "PLAYWRIGHT_MAX_PAGES_PER_CONTEXT": 8,
    }

    def start_requests(self):
        json_file_path = os.path.join(os.path.dirname(__file__), "..", "articles_internacional_urls.json")
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry in data:
            url = entry #.get("url")
            if url:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse,
                    meta={
                        "playwright": True,
                        "playwright_page_methods": [
                            PageMethod("wait_for_selector", "div.post-details", timeout=50000)
                        ],
                        "entry": entry,
                    },
                    dont_filter=True
                )

    def parse(self, response):
        news_item = NewsItem()

        # Extract category from the URL path
        path_parts = urlparse(response.url).path.strip("/").split("/")
        category_name = path_parts[0] if len(path_parts) > 0 else ""

        news_item["category"] = category_name
        news_item["sub_category"] = ""
        news_item["subcription"] = ""
        news_item["url"] = response.url
        news_item["date_raw"] = response.css(
            "div.w-full.flex.justify-center.mb-10 div.grid.grid-cols-12 div.flex.justify-between.font-Inter-Regular div::text"
        ).get()
        news_item["date_parsed"] = datetime.now().date().isoformat()
        news_item["author"] = response.css(
            "div.w-full.flex.justify-center.mb-10 div.grid.grid-cols-12 div.flex.justify-between.font-Inter-Regular span::text"
        ).get()
        news_item["title"] = response.css("h1::text").get()
        news_item["article_header"] = response.css("div.font-Lora-Regular::text").get()
        news_item["content"] = "\n".join(
            " ".join(p.xpath(".//text()").getall()).strip() for p in response.css("div.post-details")
        )

        yield news_item