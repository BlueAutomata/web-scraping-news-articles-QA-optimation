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
            yield Request(
                url=url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("evaluate", """
                            (async () => {
                                const delay = ms => new Promise(res => setTimeout(res, ms));
                                const maxCycles = 6; // total number of scroll cycles
                                const stepsPerCycle = 15; // small smooth scroll steps per cycle
                                const stepSize = 200; // pixels per step
                                const smoothDelay = 100; // delay between steps in ms

                                for (let i = 0; i < maxCycles; i++) {
                                    console.log(`Cycle ${i + 1} of ${maxCycles}`);
                                    for (let j = 0; j < stepsPerCycle; j++) {
                                        window.scrollBy(0, stepSize);
                                        await delay(smoothDelay);
                                    }
                                    await delay(2000); // wait for new content
                                }
                                console.log("✅ Finished 10 scroll cycles");
                            })();
                        """),
                        PageMethod("wait_for_timeout", 3000),
                    ],
                    errback=self.errback
                ),
                callback=self.parse_articles
            )


    async def parse_articles(self, response):
        """Extract article URLs from the loaded page."""
        for link in response.css("a.media ::attr(href)").getall():
            yield {"url": response.urljoin(link)}

    async def errback(self, failure):
        """Handle Playwright errors and close the page."""
        page = failure.request.meta.get("playwright_page")
        if page:
            await page.close()

    def parse(self, response):
        pass

