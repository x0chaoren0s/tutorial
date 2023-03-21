import scrapy, time, os, platform, logging
from utils.common_tools import getRandStr, GlobalCounter, GlobalCounter_arr
from ..items import SshServerProviderHostItem, SshServerConfigItem, Host2IpItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

# scrapy crawl sshserver4
class SSHServers4Spider(scrapy.Spider):
    name = "sshserver4"
    base_url = "https://www.vpnjantit.com"
    CRAWLED_IDX = 0
    OMMITED_IDX = 1
    fillingForm_interval_secs = 30*9+2 # 该网站要求 few mins 后才能创建下一个新用户
    # fillingForm_interval_secs = 0 # 该网站要求 1 min 后才能创建下一个新用户
    
    custom_settings = {
        # "AUTOTHROTTLE_ENABLED" : True,
        # 'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47',
        'ITEM_PIPELINES' : {
            'tutorial.pipelines.SshServerWritingJsonPipeline': 300,
        },
        'DOWNLOADER_MIDDLEWARES' : {
            'tutorial.middlewares.TutorialDownloaderMiddleware': 543,
            'tutorial.middlewares.DeferringDownloaderMiddleware': 544 # 用于使特定的 request 在特定的时间延迟后再发送
        },
        'CONCURRENT_REQUESTS' : 1, # default 16 最大并发数，该网站要求每次创建用户前后有固定间隔，因此并发数设为1，间隔时间就不用累加设置
        'ROBOTSTXT_OBEY' : False
    }

    def start_requests(self):
        list_url = 'https://www.vpnjantit.com/free-ssh-7-days'
        # yield scrapy.Request(list_url, self.parse, headers={"referer":self.base_url})
        yield scrapy.Request(list_url, self.parse, headers={"referer":self.base_url}) 

    def parse(self, response):
        '''
        产生服务商信息
        #### 爬取服务器列表页面信息Free SSH Tunnel 7 Days Servers，即每个服务器的可用性（available）（Available/MAINTENANCE）、填表页面 url、Show IP url
        ①调用 parse_server_before_fillingForm 进行填表
        #### 该网站的 host 并未在网络公共 dns 上备案，需要通过其 Show IP 连接查询真实 IP，如 Name host: ae1.vpnjantit.com  IP address: 147.78.0.131
        ②调用 parse_host2ip 产生 host2ip 信息
        '''
        yield SshServerProviderHostItem({
            'provider_host' : 'vpnjantit.com',
            'list_url'      : response.url
        })

        server_htmls = response.xpath('//div[@class="col-lg-3 col-md-6"]').getall()
        server_Selectors = [scrapy.Selector(text=html) for html in server_htmls]
        server_availables = [s.xpath('//font[@size="5"]/text()').get() for s in server_Selectors] # ['Available'/'MAINTENANCE', ...]
        server_availables = [avai=='Available' for avai in server_availables] # [True/False, ...]
        server_urls = [s.xpath('//a[@class="btn btn-primary d-block px-3 py-3 mb-4"]/@href').get() for s in server_Selectors] # ['/create-free-account?server=ae1&type=SSH', ...]
        server_urls = [self.base_url+url for url in server_urls] # ['https://www.vpnjantit.com/create-free-account?server=ae1&type=SSH', ...]
        server_showIP_urls = [s.xpath('//a[@target="_blank"]/@href').get() for s in server_Selectors] # ['/host-to-ip?host=ae1.vpnjantit.com', ...]
        server_showIP_urls = [self.base_url+url for url in server_showIP_urls] # ['https://www.vpnjantit.com/host-to-ip?host=ae1.vpnjantit.com', ...]
        server_regions = [s.xpath('//li[1]/text()').get().strip() for s in server_Selectors]
        server_hosts = [s.xpath('//li[2]/text()').get().strip() for s in server_Selectors]

        for i,available in enumerate(server_availables):
            if available:
                # logging.info(f'-----------available: {server_hosts[i]}')
                yield scrapy.Request(
                    server_urls[i], 
                    self.parse_server_before_fillingForm, 
                    headers={"referer":response.url},
                    meta = {
                        'request_interval_secs': self.fillingForm_interval_secs if  GlobalCounter_arr[self.CRAWLED_IDX].show()>0 else 0,
                        'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].count()
                    }  # meta 数据用于给 DeferringDownloaderMiddleware 传参
                )
                yield scrapy.Request(
                    server_showIP_urls[i], 
                    self.parse_host2ip, 
                    headers={"referer":response.url}
                )
            else: # available==False
                yield SshServerConfigItem({
                    'region'          : server_regions[i].strip(),
                    'host'            : server_hosts[i].strip(),
                    'error_info'      : 'no available'
                })
    
    def parse_host2ip(self, response):
        _ = response.xpath('//font[@color="green"]/text()').getall() # ['Name host: ae1.vpnjantit.com', '\nIP address: \n147.78.0.131 ']
        host = _[0].split(':')[-1].strip() # 'ae1.vpnjantit.com'
        ip = _[1].split(':')[-1].strip() # '147.78.0.131'
        yield Host2IpItem({
            'host'  : host,
            'ip'    : ip
        })

    def parse_server_before_fillingForm(self, response):
        ''' 填表以及通过 recaptcha '''
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        host = response.xpath('//h5[2]/text()').get().strip()   # br2.vpnjantit.com
        host_area = host.split('.')[0]  # br2
        yield scrapy.FormRequest.from_response(
            response,
            formdata={
                'user': getRandStr(12-1-len(host_area))+f'0{host_area}',
                'pass': getRandStr(12),
                'g-recaptcha-response': recaptcha_res
            },
            callback=self.parse_server_after_fillingForm
        )
        
    def parse_server_after_fillingForm(self, response):
        ''' 爬取注册账户后服务器的配置信息 '''
        if platform.system() != 'Windows': # windows 没有 time.tzset()，但是 windows 一般时区是正确的，不用设置
            os.environ['TZ']='GMT-8' # 设置成中国所在的东八区时区
            time.tzset()
        try:
            success_info = response.xpath('//h5/text()').getall()
            yield SshServerConfigItem({
                'region'          : success_info[3].strip(),
                'username'        : success_info[0].strip(),
                'password'        : success_info[1].strip(),
                'host'            : success_info[4].strip(),
                'date_created'    : time.strftime("%Y-%m-%d",time.localtime()), # 这个网址不显示账户的注册时间，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
                'date_expired'    : success_info[2].strip(),
                'max_logins'      : success_info[9].split(' ')[0]
            })
        except:
            try:
                server_info = response.xpath('//h5/text()').getall()
                fail_info = response.xpath('//h4//text()').get()
                yield SshServerConfigItem({
                        'region'          : server_info[0].strip(),
                        'host'            : server_info[3].strip(),
                        'error_info'      : fail_info.strip()
                    })
            except:
                try:
                    server_info = response.xpath('//h5/text()').getall()
                    fail_info = response.xpath('//font[@color="red"]/text()').get().strip()
                    yield SshServerConfigItem({
                            'region'          : server_info[0].strip(),
                            'host'            : server_info[3].strip(),
                            'error_info'      : fail_info.strip()
                        })
                except:
                    with open(f'{GlobalCounter.count()}.html', 'wb') as f:
                    # with open(f'{time.strftime("%Y-%m-%d_%H:%M:%S",time.localtime())}.html', 'wb') as f:
                        f.write(response.body)