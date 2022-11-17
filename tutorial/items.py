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
    '''
    #### 提供免费 ssh server 服务的服务商信息
    有 2 个字段：provider_host、list_url
    '''
    provider_host = scrapy.Field()
    list_url      = scrapy.Field()

class SshServerConfigItem(scrapy.Item):
    region          = scrapy.Field()
    username        = scrapy.Field()
    password        = scrapy.Field()
    host            = scrapy.Field()
    host_cloudflare = scrapy.Field()
    ip              = scrapy.Field() # 有的网站其 host 不能用，而要使用 ip，如 www.vpnjantit.com
    port            = scrapy.Field() # 有的网站不是 22，如 https://sshstores.net/
    date_created    = scrapy.Field()
    date_expired    = scrapy.Field()
    max_logins      = scrapy.Field()
    glider_config   = scrapy.Field() # forward=ssh://username:password@host:22  edit in class SshServerWritingJsonPipeline
    date_span       = scrapy.Field() # # 2022-07-12 - 2022-07-19
    error_info      = scrapy.Field()

class Host2IpItem(scrapy.Item):
    '''
    有的网站其 host 不能用，而要使用 ip，如 www.vpnjantit.com 。
    有 2 个字段：host、ip    
    '''
    host            = scrapy.Field()
    ip              = scrapy.Field()
