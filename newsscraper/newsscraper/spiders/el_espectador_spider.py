import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
from urllib.parse import urlparse
import os
import re


class ElEspectadorSpiderSpider(scrapy.Spider):
    name = "el_espectador_spider"
    allowed_domains = ["www.elespectador.com"]
    start_urls = ["https://www.elespectador.com/archivo/politica/",
                  "https://www.elespectador.com/archivo/judicial/", 
                  "https://www.elespectador.com/archivo/economia/",
                  "https://www.elespectador.com/archivo/mundo/",
                  "https://www.elespectador.com/archivo/bogota/"]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta = {
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", 'a[rel="next"]'),
                        # or PageMethod("wait_for_load_state", "networkidle") etc.
                    ],
                    "category": os.path.basename(urlparse(url).path.rstrip('/'))
                },  # enable Playwright for this request
                
                
            )

    def parse(self, response):
        category_name = response.meta.get("category", None)
        next_page = response.css("a[rel='next']::attr(href)").get()
        
        news_items = response.css("div.Card-ImagePosition")
        for news_item in news_items:
            raw_date = news_item.css("p.Card-Datetime::text").get()
            
            if raw_date:
                # Remove leading/trailing spaces and non-breaking spaces
                raw_date_clean = raw_date.replace("\xa0", " ").strip()
                
                # Use your original regex pattern for format validation
                date_match = re.search(r"^(0[1-9]|[12][0-9]|3[01])/(0[1-9]|1[0-2])/([0-9]{4})$", raw_date_clean)
                
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
            
            yield {
                "Category": category_name,
                "Sub-Category": news_item.css("h4.Card-Section a::text").get(),
                "Suscriptores": news_item.css("h4.Card-Section a::text").get(),
                "Title": news_item.css("span.Card-ExclusiveContainer::text").get(),
                "Description": news_item.css("div.Card-Hook a::text").get(),
                "Link": response.urljoin(news_item.css("h2.Card-Title a::attr(href)").get()),
                "Date_raw": raw_date_clean,
                "Date_parsed": parsed_date,
                "Author": news_item.css("h3.Card-Author a::text").get(),
            }

        if next_page is not None and "3" not in next_page:
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
        },
    )


# Link https://youtu.be/mBoX_JCKZTE?t=2708

# <a href="/archivo/politica/2/" rel="next" class="Button Button_noText Button_text Button_text_neutral">

# <span class="Card-ExclusiveContainer">Suscriptores</span>