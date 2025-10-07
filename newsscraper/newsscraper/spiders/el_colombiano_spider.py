import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
from newsscraper.items import NewsItem
import os


class ElColombianoSpiderSpider(scrapy.Spider):
    name = "el_colombiano_spider"
    allowed_domains = ["www.elcolombiano.com"]
    start_urls = [
        "https://www.elcolombiano.com/colombia/politica",
        "https://www.elcolombiano.com/colombia/salud",
        "https://www.elcolombiano.com/colombia/educacion",
        "https://www.elcolombiano.com/negocios/empresas",
        "https://www.elcolombiano.com/negocios/finanzas",
        "https://www.elcolombiano.com/negocios/agro",
        "https://www.elcolombiano.com/cultura/cine",
        "https://www.elcolombiano.com/cultura/literatura",
        "https://www.elcolombiano.com/cultura/musica"
        "https://www.elcolombiano.com/internacional/america-latina",
        "https://www.elcolombiano.com/internacional/eeuu",
        "https://www.elcolombiano.com/internacional/venezuela",
        "https://www.elcolombiano.com/internacional/europa",
        "https://www.elcolombiano.com/internacional/medio-oriente"
        ]

    max_clicks = 10  # control how many times to click

    def start_requests(self):
        for url in self.start_urls:
            page_methods = []
            for i in range(self.max_clicks):
                page_methods.extend([
                    PageMethod("evaluate", "window.scrollBy(0, document.body.scrollHeight)"),
                    PageMethod("click", "div.more-button"),
                    # wait until there are at least i+N articles
                    PageMethod(
                        "wait_for_function",
                        f"() => document.querySelectorAll('article').length > {10*(i+1)}",
                        timeout=10000,
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
        news_item["date_parsed"] = datetime.now().date().isoformat()
        news_item["author"] = response.css("div.div_author_r_texto_ div::text").get()
        news_item["title"] = " ".join([t.strip() for t in response.css("h1.ecr_articulo_titulo_multimedia__div *::text").getall() if t.strip()])
        news_item["article_header"] = response.css('p.lead.cita::text').get()
        news_item["content"] = "\n".join(" ".join(p.xpath(".//text()").getall()).strip() for p in response.css("div.paragraph p") )

        yield news_item
