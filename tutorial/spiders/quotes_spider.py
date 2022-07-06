import scrapy

class QuotesSpider(scrapy.Spider):
    name = 'quotes'

    def start_requests(self):
        name = 'quotes'
        start_urls = [
            'https://quotes.toscrape.com/page/1'
        ]
        def start_requests(self):
            urls = [
                'http://quotes.toscrape.com/page/1/',
                'http://quotes.toscrape.com/page/2/',
            ]
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse, meta={'proxy': 'http://10.92.104.204:7605'})

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'text': quote.css('span.text::text').extract_first(),
                'author': quote.css('span small::text').extract_first(),
                'tags': quote.css('div.tags a.tag::text').extract(),
            }
