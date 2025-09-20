import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
from newsscraper.items import NewsItem
import os


class ElColombianoSpiderSpider(scrapy.Spider):
    name = "el_colombiano_spider"
    allowed_domains = ["www.elcolombiano.com"]
    start_urls = ["https://www.elcolombiano.com/colombia/politica"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    # Use domcontentloaded instead of networkidle
                    "playwright_page_goto_kwargs": {
                        "wait_until": "domcontentloaded",
                        "timeout": 60000,  # 60s, adjust as needed
                    },
                    "category": os.path.basename(urlparse(url).path.rstrip('/'))
                }
            )


    def parse(self, response):
        category_name = response.meta.get("category")
        news_items = response.css('article.article.element.full-access.norestricted')
        for news_item in news_items:
            article_url = response.urljoin(news_item.css('a::attr(href)').get())
            
            # Pass basic info to article page
            meta_data = {
                "playwright": True,
                "category":  news_item.css('div.categorie__noticia__metadato a::text').get(),
                "sub_category": category_name,
                "subcription": "",
            }

            if article_url:
                yield scrapy.Request(
                    article_url,
                    callback=self.parse_news_page,
                    meta=meta_data
                )

    def parse_news_page(self, response):
        news_item = NewsItem()
        category_name = response.meta.get("category")
   

        news_item["category"] = category_name
        news_item["sub_category"] = response.meta.get("sub_category")
        news_item["subcription"] = ""
        news_item["url"] = response.url
        news_item["date_raw"] = response.css('span.hora-noticia::text').get()
        news_item["date_parsed"] = response.css('span.hora-noticia::text').get()
        news_item["author"] = response.css("div.div_author_r_texto_ div::text").get()
        news_item["title"] = response.css('h1.ecr_articulo_titulo_multimedia__div span::text').get()
        news_item["article_header"] = response.css('p.lead.cita::text').get()
        news_item["content"] = "\n".join(" ".join(p.xpath(".//text()").getall()).strip()     for p in response.css("div.paragraph p") )

        yield news_item
