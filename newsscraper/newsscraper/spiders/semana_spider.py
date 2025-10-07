import scrapy
import os

from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
from newsscraper.items import NewsItem

class SemanaSpiderSpider(scrapy.Spider):
    name = "semana_spider"
    allowed_domains = ["www.semana.com"]
    start_urls = [#"https://www.semana.com/politica/", 
                  #"https://www.semana.com/nacion/" , 
                  #"https://www.semana.com/economia/empresas/", 
                  #"https://www.semana.com/economia/macroeconomia/", 
                  #"https://www.semana.com/economia/emprendimiento/"
                  #"https://www.semana.com/cultura/libros/"
                  #"https://www.semana.com/cultura/cine/",
                  #"https://www.semana.com/cultura/musica/",
                  #"https://www.semana.com/cultura/arte/",
                  #"https://www.semana.com/cultura/television/",
                  "https://www.semana.com/salud/"
                  ]

    max_clicks = 10  # control how many times to click

    def start_requests(self):
        for url in self.start_urls:
            page_methods = []
            for i in range(self.max_clicks):
                expected_count = 15 * (i + 1)  # 15 per click
                page_methods.extend([
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("click", "a.styles__VerMas-sc-o51gjq-3.kdpnIy"),
                    # wait until number of grid-items > expected_count
                    PageMethod(
                        "wait_for_function",
                        f"() => document.querySelectorAll('div.grid-item').length >= {expected_count}",
                        timeout=20000,
                    ),
                ])

            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_page_goto_kwargs": {"wait_until": "domcontentloaded"},
                    "playwright_page_methods": page_methods,
                    "category": os.path.basename(urlparse(url).path.rstrip('/'))
                },
                callback=self.parse
            )


    def parse(self, response):
        with open("page_debug.html", "wb") as f:
            f.write(response.body)

        category_name = response.meta.get("category")
        news_items = response.css("main.main-section div.section div.grid-box.grid-2-md.grid-4-lg div.grid-wrap div.grid-box.grid-3-lg div.grid-item")
        for news_item in news_items:
            article_url = response.urljoin(news_item.css("h2.card-title.h4 a::attr(href)").get())
            
            # Pass basic info to article page
            meta_data = {
                "playwright": True,
                "category": category_name,
                "sub_category": news_item.css("p.card-category span::text").get(),
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

        content_list = [
            p.xpath("string()").get().strip()
            for p in response.css("div.paywall.mx-auto.mb-4 p")
            if p.xpath("string()").get()
        ]

        # Join with new lines instead of spaces
        full_content = "\n".join(content_list)
   

        news_item["category"] = category_name
        news_item["sub_category"] = response.meta.get("sub_category")
        news_item["subcription"] = ""
        news_item["url"] = response.url
        news_item["date_raw"] = response.css("div.mb-5.text-xs.text-smoke-500 ::text").get()
        news_item["date_parsed"] = datetime.now().date().isoformat()
        news_item["author"] = response.css("a span.mb-1.border-l.border-primary.pl-2.text-sm.font-medium ::text").get()
        news_item["title"] = response.css("h1 ::text").get()
        news_item["article_header"] = response.css("p.mb-4.text-lg ::text").get()
        news_item["content"] = full_content

        yield news_item