import scrapy

class TmpSpider(scrapy.spiders.CrawlSpider):
    name = 'tmp'
    start_urls = [
                'https://blog.csdn.net/kuanggudejimo/article/details/103185817'
            ]

    def parse(self, response):
        yield response

# class Self:
#     def __init__(self) -> None:
#         self.name = "sshservers4"
#         self.base_url = "https://www.vpnjantit.com"
#         self.list_url = 'https://www.vpnjantit.com/free-ssh-7-days'
# self=Self()
# fetch(self.list_url)
# fetch(server_showIP_urls[i], headers={"referer":response.url})