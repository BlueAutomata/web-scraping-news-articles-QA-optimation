import scrapy
import requests
import os

from newsscraper.items import NewsItem
from datetime import datetime

API_KEY = ""
CSE_ID = ""



class LaJornadaSpiderSpider(scrapy.Spider):
    name = "la_jornada_spider"
    allowed_domains = ["jornada.com.mx"]

    def start_requests(self):
        if not API_KEY or not CSE_ID:
            self.logger.error("Missing GOOGLE_API_KEY or GOOGLE_CSE_ID_JORNADA environment variables")
            return

        queries = {
            "politica": "site:jornada.com.mx inurl:/noticia/ inurl:/politica/",
            "economia": "site:jornada.com.mx inurl:/noticia/ inurl:/economia/",
            "cultura": "site:jornada.com.mx inurl:/noticia/ inurl:/cultura/",
            "mundo": "site:jornada.com.mx inurl:/noticia/ inurl:/mundo/",
        }

        for category, query in queries.items():
            for start in range(1, 151, 10):  # 1 and 11 = 20 results max
                url = (
                    f"https://www.googleapis.com/customsearch/v1?"
                    f"q={query}&key={API_KEY}&cx={CSE_ID}&start={start}"
                )

                response = requests.get(url).json()

                # Debug: log API errors
                if "error" in response:
                    self.logger.error(f"Google API error: {response['error']}")
                    continue

                urls = [item["link"] for item in response.get("items", [])]

                for link in urls:
                    yield scrapy.Request(
                        url=link,
                        callback=self.parse,
                        cb_kwargs={"category": category}
                    )

    def parse(self, response, category):
        news_item = NewsItem()

        news_item["category"] = category
        news_item["sub_category"] = " ".join(t.strip() for t in response.css("div.seccion.border-bottom-4 a::text").getall() if t.strip())
        news_item["subcription"] = ""
        news_item["url"] = response.url
        news_item["date_raw"] = response.css("span.nota-fecha ::text").get()
        news_item["date_parsed"] = datetime.now().date().isoformat()
        news_item["author"] = response.css("div.nota-autor a ::text").get()
        news_item["title"] = response.css("h1.nota-titulo.nota-destacada ::text").get()
        news_item["article_header"] = ""
        news_item["content"] = "\n".join(" ".join(p.xpath(".//text()").getall()).strip() for p in response.css("div.nota-row p.nota-justify") )

        yield news_item

