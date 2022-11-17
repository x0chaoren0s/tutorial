import scrapy
from utils.common_tools import getRandStr, normalized_local_date, GlobalCounter
from ..items import SshServerProviderHostItem, SshServerConfigItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

# scrapy crawl sshservers6
class SSHServers6Spider(scrapy.Spider):
    name = "sshservers6"
    base_url = "https://sshstores.net"
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        "AUTOTHROTTLE_ENABLED" : True,
        'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47',
        'ITEM_PIPELINES' : {
            'tutorial.pipelines.SshServerWritingJsonPipeline': 300,
        },
        'ROBOTSTXT_OBEY' : False
    }

    def start_requests(self):
        list_url = 'https://sshstores.net/ssh-region' # 仅存储地区列表页面url
        yield scrapy.Request(list_url, self.parse, headers={"referer":self.base_url})

    def parse(self, response):
        '''
        爬取地区列表页面，产生服务器供应商信息，
        并调用 parse_region 爬取各区域的服务器信息
        '''
        provider_host = response.xpath('//meta[@name="copyright"]/@content').get()
        yield SshServerProviderHostItem({
            'provider_host': provider_host,
            'list_url'     : response.url
        })

        region_names = response.xpath('//h4[@class="font-weight-bold"]/text()').getall()
        region_urls = response.xpath('//a[@class="btn btn-purple-soft btn-marketing rounded-pill"]/@href').getall()
        region_urls = [self.base_url+r for r in region_urls]
        # yield from response.follow_all(region_urls, self.parse_region)
        for region,url in zip(region_names, region_urls):
            yield scrapy.Request(
                url, 
                self.parse_region, 
                headers={"referer":response.url},
                meta = {
                    'region': region, # 该网站注册成功页面没有服务器的地区信息，因此在这里传参过去
                    # 'request_interval_secs': self.fillingForm_interval_secs,  # 用于给 DeferringDownloaderMiddleware 传参
                    # 'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].show() # 用于给 DeferringDownloaderMiddleware 传参
                }  
            )

    def parse_region(self, response):
        '''
        爬取地区页面内各服务器信息，对还有容量的服务器（available）
        调用 parse_server_before_fillingForm 进行填表
        '''
        server_strs = response.xpath('//div[@class="col-md-3 mb-5"]').getall() # 是一个str的list
        server_strs = list(set(server_strs)) # 这个网站的页面可能有重复的服务器，用set去重
        server_selectors = [scrapy.Selector(text=svr) for svr in server_strs] # str 转回 selector
        # servers_infos = [[
        #     svr.xpath('//p/text()').getall()[1].split()[0], # host
        #     (lambda s:s.isdigit() and int(s)>0)(svr.xpath('//span//text()').get()), # avalaible: True or False
        #     svr.xpath('//a/@href').get() # href：该服务器的填表页面
        # ] for svr in servers_selectors] # 总体是一个list放各个服务器信息，每个服务器的信息也是一个list放host、available、href
        server_hosts = [s.xpath('//div[@class="card-text"][1]/text()').get().split(':')[-1].strip() for s in server_selectors]
        server_ports = [s.xpath('//div[@class="card-text"][6]/text()').get().split(':')[-1].strip() for s in server_selectors] # 这个网站的ssh不是用22端口
        server_remains = [s.xpath('//div[@class="badge badge-pill badge-danger-soft text-server badge-marketing mb-3"]/text()').get().split(' ')[0].strip()
            for s in server_selectors] # ['Full', '2', '0', ..]
        server_availables = [r!='Full' for r in server_remains] # 经测试 Full 不能创建，0可以
        server_urls = [s.xpath('//a[@class="btn btn-primary btn-marketing rounded-pill"]/@href').get() for s in server_selectors]
        server_urls = [self.base_url+r for r in server_urls]

        for avai,url,host,port in zip(server_availables, server_urls, server_hosts, server_ports):
            if avai: # avalaible: True
                yield scrapy.Request(
                    url, 
                    self.parse_server_before_fillingForm, 
                    headers={"referer":response.url},
                    meta = {
                        'region'    : response.meta['region'], # 该网站注册成功页面没有服务器的地区信息，因此在这里传参过去
                        'port'      : port,  # 这个网站的ssh不是用22端口
                        'host'      : host      # 用于recaptcha求错的时候记录到输出文件
                        # 'request_interval_secs': self.fillingForm_interval_secs,  # 用于给 DeferringDownloaderMiddleware 传参
                        # 'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].show() # 用于给 DeferringDownloaderMiddleware 传参
                    }  
                )
            else: # avalaible: False
                yield SshServerConfigItem({
                    'region'          : response.meta['region'],
                    'host'            : host,
                    'error_info'      : 'no available'
                })


    def parse_server_before_fillingForm(self, response):
        ''' 填表以及通过 recaptcha '''
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        yield scrapy.FormRequest.from_response(
            response,
            formdata={
                'username': getRandStr(12),
                'password': getRandStr(12),
                'g-recaptcha-response': recaptcha_res
            },
            callback=self.parse_server_after_fillingForm,
            meta = {
                'region'    : response.meta['region'], # 该网站注册成功页面没有服务器的地区信息，因此在这里传参过去
                'port'      : response.meta['port'],  # 这个网站的ssh不是用22端口
                'host'      : response.meta['host']      # 用于recaptcha求错的时候记录到输出文件
                # 'request_interval_secs': self.fillingForm_interval_secs,  # 用于给 DeferringDownloaderMiddleware 传参
                # 'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].show() # 用于给 DeferringDownloaderMiddleware 传参
            } 
        )
        
    def parse_server_after_fillingForm(self, response):
        ''' 爬取注册账户后服务器的配置信息 '''
        if response.text.find('Failed Captcha Verification')!=-1:
            yield SshServerConfigItem({
                'region'          : response.meta['region'],
                'host'            : response.meta['host'],
                'error_info'      : 'Failed Captcha Verification'
            })
        elif response.text.find('Oops server did not respond please try another server..!')!=-1:
            yield SshServerConfigItem({
                'region'          : response.meta['region'],
                'host'            : response.meta['host'],
                'error_info'      : 'server did not respond'
            })
        else:
            yield SshServerConfigItem({
                'region'          : response.meta['region'],
                'username'        : response.xpath('//ul[@class="list-unstyled text-left"]/li[3]/strong/text()').get(),
                'password'        : response.xpath('//ul[@class="list-unstyled text-left"]/li[4]/strong/text()').get(),
                'host'            : response.xpath('//ul[@class="list-unstyled text-left"]/li[1]/strong/text()').get(),
                'host_cloudflare' : response.xpath('//ul[@class="list-unstyled text-left"]/li[2]/strong/text()').get(),
                'port'            : response.meta['port'],
                'date_created'    : normalized_local_date(), # 这个网址不显示账户的注册时间，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
                'date_expired'    : response.xpath('//ul[@class="list-unstyled text-left"]/li[6]/strong/text()').get()
            })