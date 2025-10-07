from requests import Request
import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
import os

from newsscraper.items import NewsItem


import scrapy
from scrapy import Request
from scrapy_playwright.page import PageMethod


class ElExcelsiorSpiderSpider(scrapy.Spider):
    name = "el_excelsior_spider"
    allowed_domains = ["www.excelsior.com.mx"]
    start_urls = [
        "https://www.excelsior.com.mx/politica",
        "https://www.excelsior.com.mx/global",
        "https://www.excelsior.com.mx/musica",
        "https://www.excelsior.com.mx/television",
        "https://www.excelsior.com.mx/cine",
        "https://www.excelsior.com.mx/series-de-television",
        "https://www.excelsior.com.mx/salud"
        ]

    def start_requests(self):
        for url in self.start_urls:
            category = os.path.basename(urlparse(url).path.rstrip('/'))
            yield Request(
                url=url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    category=category,  # ✅ pass category to next callback
                    playwright_page_methods=[
                        PageMethod("evaluate", """
                            (async () => {
                                const delay = ms => new Promise(res => setTimeout(res, ms));
                                const maxCycles = 6; // total number of scroll cycles
                                const stepsPerCycle = 15; // smooth scroll steps per cycle
                                const stepSize = 200; // pixels per step
                                const smoothDelay = 100; // delay between steps

                                for (let i = 0; i < maxCycles; i++) {
                                    console.log(`Cycle ${i + 1} of ${maxCycles}`);
                                    for (let j = 0; j < stepsPerCycle; j++) {
                                        window.scrollBy(0, stepSize);
                                        await delay(smoothDelay);
                                    }
                                    await delay(2000); // wait for new content
                                }
                                console.log("✅ Finished smooth scrolling");
                            })();
                        """),
                        PageMethod("wait_for_timeout", 3000),
                    ],
                    errback=self.errback
                ),
                callback=self.parse_articles
            )

    def parse_articles(self, response):
        category_name = response.meta.get("category")

        news_items = response.css("a.content a")
        for news_item in news_items:
            article_url = response.urljoin(news_item.css('a::attr(href)').get())
            
            # Pass basic info to article page
            meta_data = {
                "playwright": True,
                "category":  category_name,
                "sub_category": news_items.css("small.text-muted.bottom-text span::text").get(),
                "subcription": "",
            }

            if article_url:
                yield scrapy.Request(
                    article_url,
                    callback=self.parse_news_page,
                    meta=meta_data
                )

    async def errback(self, failure):
        """Handle Playwright errors and close the page."""
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()

    def parse_news_page(self, response):
        news_item = NewsItem()
        category_name = response.meta.get("category")
   

        news_item["category"] = category_name
        news_item["sub_category"] = response.css('span.header-node span::text').get()
        news_item["subcription"] = ""
        news_item["url"] = response.url
        news_item["date_raw"] = response.css('span.hour time::text').get()
        news_item["date_parsed"] = datetime.now().date().isoformat()
        news_item["author"] = response.css("span.author-name ::text").get()
        news_item["title"] = " ".join([t.strip() for t in response.css("h1.title *::text").getall() if t.strip()])
        news_item["article_header"] = response.css('h2.teaser ::text').get()
        news_item["content"] = "\n".join(" ".join(p.xpath(".//text()").getall()).strip() for p in response.css("div.field-items p") )

        yield news_item
