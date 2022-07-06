import scrapy

class TmpSpider(scrapy.spiders.CrawlSpider):
    name = 'tmp'
    start_urls = [
                'https://blog.csdn.net/kuanggudejimo/article/details/103185817'
            ]

    def parse(self, response):
        yield response
