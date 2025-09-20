import scrapy


class ExcelsiorSpiderSpider(scrapy.Spider):
    name = "excelsior_spider"
    allowed_domains = ["www.excelsior.com.mx"]
    start_urls = ["https://www.excelsior.com.mx/"]

    def parse(self, response):
        pass
