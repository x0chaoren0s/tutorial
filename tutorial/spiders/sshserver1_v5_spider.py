import scrapy, time, asyncio
from utils.common_tools import getRandStr, GlobalCounter_arr
from ..items import SshServerProviderHostItem, SshServerConfigItem

# scrapy crawl sshservers1_v5
class SSHServers1V5Spider(scrapy.Spider):
    name = "sshservers1_v5"
    fillingForm_interval_secs = 60+2  # 该网站要求60s后再创建一个新用户
    CRAWLED_IDX = 0 # 用于计数已爬取的有效服务器，配合上述 fillingForm_interval_secs 进行暂停
    custom_settings = {
        # 'DOWNLOAD_DELAY': 70, # 该网站要求60s后再创建一个新用户
        "AUTOTHROTTLE_ENABLED" : True,
        'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47',
        'ITEM_PIPELINES' : {
            'tutorial.pipelines.SshServerWritingJsonPipeline': 300,
        },
        'DOWNLOADER_MIDDLEWARES' : {
            'tutorial.middlewares.TutorialDownloaderMiddleware': 543,
            'tutorial.middlewares.DeferringDownloaderMiddleware': 544 # 用于使特定的 request 在特定的时间延迟后再发送
        },
        'CONCURRENT_REQUESTS' : 1 # default 16 最大并发数，该网站要求每次创建用户前后有固定间隔，因此并发数设为1，间隔时间就不用累加设置
    }

    def start_requests(self):
        list_url = 'https://www.mytunneling.com/ssh-server-30' # 仅存储服务器列表页面 url
        yield scrapy.Request(list_url, self.parse, headers={"referer": 'https://www.mytunneling.com'})

    def parse(self, response):
        '''
        爬取服务器列表页面，产生服务器供应商信息，获得各服务器 serverid 和所在区域 region
        并调用 parse_server_after_fillingForm 爬取各服务器的配置
        '''
        provider_host = response.css('a.navbar-brand::text').get()
        yield SshServerProviderHostItem({
            'provider_host': provider_host,
            'list_url'     : response.url
        })

        # 服务器配置页面 url，但不需要真的访问，只需要从中提取 serverid，
        # 真正的提交页面并非上述 url，而是 https://www.mytunneling.com/create-account-ssh-30.php
        servers_urls = response.css('div.row a::attr(href)').getall()
        servers_ids  = [url.split('/')[-2] for url in servers_urls]
        # 服务器所在区域
        servers_regions = response.xpath('//div[@class="row"]//ul/li[2]/text()').getall()
        servers_regions = [r[16:] for r in servers_regions] # "Server Location Germany" -> "Germany"
        for (serverid, region) in zip(servers_ids, servers_regions):
            #         asyncio.run(asyncio.sleep(self.fillingForm_interval_secs))
            yield scrapy.FormRequest(
                url='https://www.mytunneling.com/create-account-ssh-30.php',
                formdata = {'serverid': serverid, 'username': getRandStr(), 'password': getRandStr()},
                callback = self.parse_server_after_fillingForm,
                cb_kwargs = {'region': region},
                meta = {
                    'request_interval_secs': self.fillingForm_interval_secs if GlobalCounter_arr[self.CRAWLED_IDX].count()>1 else 0,
                    'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].show()
                }  # meta 数据用于给 DeferringDownloaderMiddleware 传参
            )
        
    def parse_server_after_fillingForm(self, response, region):
        ''' 爬取注册账户后服务器的配置信息 '''
        body_strlist = response.xpath('//text()').getall()
        if len(body_strlist) == 1:
            return SshServerConfigItem({
                'error_info': body_strlist[0]
            })

        def normalize_date(datestr): # 如把 05-June-2022 标准化成 2022-06-05
            return time.strftime("%Y-%m-%d",time.strptime(datestr,"%d-%B-%Y"))
        return SshServerConfigItem({
            'region':       region,
            'username':     body_strlist[1],
            'password':     body_strlist[4].split(':')[1].split()[0],
            'host':         body_strlist[5].split(':')[1].split()[0],
            'date_created': normalize_date(body_strlist[6].split(':')[1].split()[0]),
            'date_expired': normalize_date(body_strlist[7].split(':')[1].split()[0])
        })