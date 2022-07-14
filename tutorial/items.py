# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TutorialItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class SshServerProviderHostItem(scrapy.Item):
    provider_host = scrapy.Field()
    list_url      = scrapy.Field()

class SshServerConfigItem(scrapy.Item):
    region          = scrapy.Field()
    username        = scrapy.Field()
    password        = scrapy.Field()
    host            = scrapy.Field()
    host_cloudflare = scrapy.Field()
    date_created    = scrapy.Field()
    date_expired    = scrapy.Field()
    max_logins      = scrapy.Field()
    glider_config   = scrapy.Field() # forward=ssh://username:password@host:22  edit in class SshServerWritingJsonPipeline
    date_span       = scrapy.Field() # # 2022-07-12 - 2022-07-19
    error_info      = scrapy.Field()

