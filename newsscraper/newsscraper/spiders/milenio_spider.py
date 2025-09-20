import scrapy


class MilenioSpiderSpider(scrapy.Spider):
    name = "milenio_spider"
    allowed_domains = ["www.milenio.com"]
    start_urls = ["https://www.milenio.com/"]

    def parse(self, response):
        pass
