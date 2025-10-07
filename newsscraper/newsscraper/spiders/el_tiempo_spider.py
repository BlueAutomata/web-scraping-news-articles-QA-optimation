import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
import os

from newsscraper.items import NewsItem

class ElTiempoSpiderSpider(scrapy.Spider):
    name = "el_tiempo_spider"
    allowed_domains = ["www.eltiempo.com"]
    start_urls = ["https://www.eltiempo.com/politica/",
                  "https://www.eltiempo.com/economia",
                  "https://www.eltiempo.com/salud",
                  "https://www.eltiempo.com/mundo",
                  "https://www.eltiempo.com/cultura"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "category": os.path.basename(urlparse(url).path.rstrip('/'))
                }
            )

    def parse(self, response):
        category_name = response.meta.get("category")
        
        # Extract articles on the archive page
        news_items = response.css("div.c-board-mas-noticias__grid div.c-board-mas-noticias__articulo")
        for news_item in news_items:
            article_url = response.urljoin(news_item.css("a.c-articulo__titulo__txt ::attr(href)").get())
            
            # Pass basic info to article page
            meta_data = {
                "playwright": True,
                "autor": news_item.css("a.c-articulo__detalle__txt ::text").get(),
                "category": category_name,
                "sub_category": "",
            }

            if article_url:
                yield scrapy.Request(
                    article_url,
                    callback=self.parse_news_page,
                    meta=meta_data
                )
        
        # Pagination
        next_page = response.css("a.c-pagination__next::attr(href)").get()
        if next_page is not None and "21#" not in next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(
                next_page_url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "category": category_name
                }
            )

    # <h1 class="Title ArticleHeader-Title">

    def parse_news_page(self, response):
        news_item = NewsItem()
        category_name = response.meta.get("category")
   

        news_item["category"] = category_name
        news_item["sub_category"] = response.meta.get("sub_category")
        news_item["subcription"] = response.css("div.c-tag-suscriptor__texto p::text").get()
        news_item["url"] = response.url
        news_item["date_raw"] = response.css("p.c-articulo__autor__grupo span.c-articulo__autor__fecha time::text").get()
        news_item["date_parsed"] =  datetime.now().date().isoformat()
        news_item["author"] = response.meta.get("autor")
        news_item["title"] = response.css("h1.c-articulo__titulo::text").get()
        news_item["article_header"] = response.css("h2.c-lead__titulo ::text").get()
        news_item["content"] =  "\n".join(" ".join(p.xpath(".//text()").getall()).strip() for p in response.css("div.paragraph"))

        yield news_item
