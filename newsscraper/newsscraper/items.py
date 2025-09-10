# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NewsscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class NewsItem(scrapy.Item):
    category = scrapy.Field()
    sub_category = scrapy.Field()
    subcription = scrapy.Field()
    url = scrapy.Field()
    date_raw = scrapy.Field()
    date_parsed = scrapy.Field()
    author = scrapy.Field()
    title = scrapy.Field()
    article_header = scrapy.Field()
    content = scrapy.Field()

def to_lower(text: str) -> str:
    if text is None:
        return ""
    return text.lower()