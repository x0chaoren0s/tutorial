import scrapy, time
from utils.common_tools import getRandStr, GlobalCounter
from ..items import SshServerProviderHostItem, SshServerConfigItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

# scrapy crawl sshservers2
class SSHServers2Spider(scrapy.Spider):
    name = "sshservers2"
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        "AUTOTHROTTLE_ENABLED" : True,
        'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47',
        'ITEM_PIPELINES' : {
            'tutorial.pipelines.SshServerWritingJsonPipeline': 300,
        }
    }

    def start_requests(self):
        list_url = 'https://vpnhack.com/ssh' # 仅存储服务器列表页面url
        yield scrapy.Request(list_url, self.parse)

    def parse(self, response):
        '''
        爬取地区列表页面，产生服务器供应商信息，
        并调用 parse_region 爬取各区域的服务器信息
        '''
        provider_host = response.xpath('//a[@class="navbar-brand"]/@href').get().split('//')[1]
        yield SshServerProviderHostItem({
            'provider_host': provider_host,
            'list_url'     : response.url
        })

        region_urls = response.xpath('//a[@class="btn btn-primary d-block rounded-pill"]/@href').getall()
        yield from response.follow_all(region_urls, self.parse_region)

    def parse_region(self, response):
        '''
        爬取地区页面内各服务器信息，对还有容量的服务器（available）
        调用 parse_server_before_fillingForm 进行填表
        '''
        servers_strs = response.xpath('//div[@class="clean-pricing-item"]').getall() # 是一个str的list
        servers_strs = list(set(servers_strs)) # 这个网站的页面可能有重复的服务器，用set去重
        servers_selectors = [scrapy.Selector(text=svr) for svr in servers_strs] # str 转回 selector
        servers_infos = [[
            svr.xpath('//p/text()').getall()[1].split()[0], # host
            (lambda s:s.isdigit() and int(s)>0)(svr.xpath('//span//text()').get()), # avalaible: True or False
            svr.xpath('//a/@href').get() # href：该服务器的填表页面
        ] for svr in servers_selectors] # 总体是一个list放各个服务器信息，每个服务器的信息也是一个list放host、available、href
        for svrinfo in servers_infos:
            if svrinfo[1]: # avalaible: True
                yield scrapy.Request(svrinfo[2], self.parse_server_before_fillingForm)
            else: # avalaible: False
                yield SshServerConfigItem({
                    'region'          : response.url.split('/')[-1],
                    'host'            : svrinfo[0],
                    'error_info'      : 'no available'
                })


    def parse_server_before_fillingForm(self, response):
        ''' 填表以及通过 recaptcha '''
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'username': getRandStr(12+6),
                'password': getRandStr(12),
                'g-recaptcha-response': recaptcha_res,
                'submit': ''
            },
            callback=self.parse_server_after_fillingForm
        )
        
    def parse_server_after_fillingForm(self, response):
        ''' 爬取注册账户后服务器的配置信息 '''
        def normalize_date(datestr): # 如把 6 Jun 2022 标准化成 2022-06-06
            return time.strftime("%Y-%m-%d",time.strptime(datestr,"%d %b %Y"))
        try:
            return SshServerConfigItem({
                'region'          : response.url.split('/')[-2],
                'username'        : response.xpath('//div[@class="alert alert-success text-center"]//li[3]/b/text()').get(),
                'password'        : response.xpath('//div[@class="alert alert-success text-center"]//li[4]/b/text()').get(),
                'host'            : response.xpath('//div[@class="alert alert-success text-center"]//li[1]/b/text()').get(),
                'host_cloudflare' : response.xpath('//div[@class="alert alert-success text-center"]//li[2]/b/text()').get(),
                'date_created'    : normalize_date(response.xpath('//div[@class="alert alert-success text-center"]//li[5]/b/text()').get()),
                'date_expired'    : normalize_date(response.xpath('//div[@class="alert alert-success text-center"]//li[6]/b/text()').get())
            })
        except Exception as e:
            try:
                return SshServerConfigItem({
                    'region'          : response.url.split('/')[-2],
                    'host'            : response.xpath('//div[@class="col-12 p-3"]/h5/text()').get().strip(),
                    'error_info'      : response.xpath('//div[@class="alert alert-warning"]/text()[2]').get().strip()
                })
            except Exception as e:
                print(e)
                with open(f'server2_{GlobalCounter.count()}.html', 'wb') as f:
                    f.write(response.body)