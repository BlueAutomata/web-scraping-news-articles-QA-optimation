import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
import os

class ElEspectadorSpider(scrapy.Spider):
    name = "el_espectador_spider"
    allowed_domains = ["www.elespectador.com"]
    start_urls = [
        "https://www.elespectador.com/archivo/politica/",
        "https://www.elespectador.com/archivo/judicial/", 
        "https://www.elespectador.com/archivo/economia/",
        "https://www.elespectador.com/archivo/mundo/",
        "https://www.elespectador.com/archivo/bogota/"
    ]

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
        category_name = response.meta.get("category")
        
        # Extract articles on the archive page
        news_items = response.css("div.Card-ImagePosition")
        for news_item in news_items:
            raw_date = news_item.css("p.Card-Datetime::text").get()
            
            if raw_date:
                # Remove leading/trailing spaces and non-breaking spaces
                raw_date_clean = raw_date.replace("\xa0", " ").strip()
                
                if raw_date:
                    # Remove leading/trailing spaces and non-breaking spaces
                    raw_date_clean = raw_date.replace("\xa0", " ").strip()
                    
                    try:
                        # Try to parse the date in DD/MM/YYYY format
                        # This handles both single-digit (8/9/2025) and two-digit (08/09/2025) formats
                        date_obj = datetime.strptime(raw_date_clean, "%d/%m/%Y")
                        parsed_date = date_obj.strftime("%d-%m-%Y")
                    except ValueError:
                        # If parsing fails, it's not a valid date format
                        parsed_date = datetime.now().strftime("%d-%m-%Y")
                else:
                    # raw_date was None or empty
                    parsed_date = datetime.now().strftime("%d-%m-%Y")
                    raw_date_clean = None

            article_url = response.urljoin(news_item.css("h2.Card-Title a::attr(href)").get())
            
            # Pass basic info to article page
            meta_data = {
                "playwright": True,
                "autor": news_item.css("h3.Card-Author a::text").get(),
                "category": category_name,
                "archive_title": news_item.css("span.Card-ExclusiveContainer::text").get(),
                "sub_category": news_item.css("h4.Card-Section a::text").get(),
                "description": news_item.css("div.Card-Hook a::text").get(),
                "raw_date": raw_date_clean,
                "parsed_date": parsed_date,
            }

            if article_url:
                yield scrapy.Request(
                    article_url,
                    callback=self.parse_news_page,
                    meta=meta_data
                )
        
        # Pagination
        next_page = response.css("a[rel='next']::attr(href)").get()
        if next_page is not None and "2" not in next_page:
            next_page_url = response.urljoin(next_page)
            yield scrapy.Request(
                next_page_url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "div.Card-ImagePosition")
                    ],
                    "category": category_name
                }
            )

    # <h1 class="Title ArticleHeader-Title">

    def parse_news_page(self, response):
        category_name = response.meta.get("category")
        # Extract all paragraphs with class "font--secondary"
        paragraphs = response.css("p.font--secondary::text").getall()
        full_content = " ".join([p.strip() for p in paragraphs if p.strip()])
        yield {
            "Category": category_name,
            "Sub-Category": response.meta.get("sub_category"),
            "Archive_Title": response.meta.get("archive_title"),
            "Description": response.meta.get("description"),
            "URL": response.url,
            "Date_raw": response.meta.get("raw_date"),
            "Date_parsed": response.meta.get("parsed_date"),
            "Author": response.meta.get("autor"),
            "Title": response.css("h1.ArticleHeader-Title::text").get(),
            "Subtitle": response.css("h2.ArticleHeader-Hook div::text").get(),
            "Content": full_content
        }
