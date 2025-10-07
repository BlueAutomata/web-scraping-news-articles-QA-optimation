import json
import scrapy
import requests
import os

from newsscraper.items import NewsItem
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse


class AnimalPoliticoSpiderSpider(scrapy.Spider):
    name = "animal_politico_spider"
    allowed_domains = ["animalpolitico.com"]
    start_urls = [
        #"https://www.animalpolitico.com/internacional/notas",
        "https://www.animalpolitico.com/hablemos-de/finanzas"
        #"https://www.animalpolitico.com/politica/notas",
        #"https://www.animalpolitico.com/salud/notas",
        #"https://www.animalpolitico.com/seguridad/notas"
    ]

    def start_requests(self):
        for url in self.start_urls:
            path_segments = [seg for seg in urlparse(url).path.split("/") if seg]
            category = path_segments[0] if len(path_segments) > 0 else ""
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "category": category,  # <-- this will be "politica"
                },
            )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        category_name = response.meta["category"]

        articles_urls = []

        for _ in range(15):  # limit to 5 pages
        # Collect article URLs from the current page
            for news_item in await page.query_selector_all("div.col-span-3"):
                href = await news_item.query_selector("a")
                if href:
                    url = await href.get_attribute("href")
                    if url:
                        articles_urls.append(response.urljoin(url))

            # Attempt to go to next page
            next_button = await page.query_selector("li.next a[rel='next']")
            if next_button:
                await next_button.click()
                await page.wait_for_load_state("domcontentloaded")
            else:
                break

        # Save collected article URLs to a JSON file
        output_file = os.path.join(os.path.dirname(__file__), "..", "articles_finanzas_urls.json")
        if os.path.exists(output_file):
            # append to existing file
            with open(output_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
            articles_urls = existing + articles_urls

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(articles_urls, f, ensure_ascii=False, indent=4)
            
        await page.close()

        # yield requests for all articles
        for url in articles_urls:
            yield scrapy.Request(
                url,
                callback=self.parse_news_page,
                meta={
                        "category": category_name,
                    },
            )


    # <h1 class="Title ArticleHeader-Title">

    def parse_news_page(self, response):
        news_item = NewsItem()
        category_name = response.meta.get("category")

        news_item["category"] = category_name
        news_item["sub_category"] = ""
        news_item["subcription"] = ""
        news_item["url"] = response.url
        news_item["date_raw"] = response.css("div.w-full.flex.justify-center.mb-10 div.grid.grid-cols-12 div.flex.justify-between.font-Inter-Regular div::text").get()
        news_item["date_parsed"] = datetime.now().date().isoformat()
        news_item["author"] = response.css("div.w-full.flex.justify-center.mb-10 div.grid.grid-cols-12 div.flex.justify-between.font-Inter-Regular span::text").get()
        news_item["title"] = response.css("h1::text").get()
        news_item["article_header"] = response.css("div.font-Lora-Regular::text").get()
        news_item["content"] = "\n".join(" ".join(p.xpath(".//text()").getall()).strip() for p in response.css("div.post-details") )

        yield news_item
