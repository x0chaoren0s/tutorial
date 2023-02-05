import scrapy, time, os, asyncio, platform
from utils.common_tools import getRandStr, GlobalCounter, GlobalCounter_arr
from ..items import SshServerProviderHostItem, SshServerConfigItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

from scrapy import Selector

import logging

# scrapy crawl sshserver3
class SSHServers3Spider(scrapy.Spider):
    name = "sshserver3"
    base_url = "https://www.jagoanssh.com/"
    # crawled_server_cnt = MyCounter() # 经实验，不同线程之间不能共享这两个变量，因此考虑使用全局变量 GlobalCounter_arr
    # ommited_server_cnt = MyCounter()
    CRAWLED_IDX = 0 # 这两个是上面两个变量对应转换到 GlobalCounter_arr 中的索引
    OMMITED_IDX = 1
    fillingForm_interval_secs = 60*5+2 # 该网站要求 5 min 后才能创建下一个新用户
    
    custom_settings = {
        # 'DOWNLOAD_DELAY': 5*60+2, 
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
        list_url = 'https://www.jagoanssh.com/' # 该网站不支持直接输入网址访问，必须从已有页面点击
        yield scrapy.Request(list_url, self.parse)

    def parse(self, response):
        '''
        爬取服务器组列表页面，该列表有4项可选：3days,7days,vip,vmess,vless,gfw,go,ss,sstp,wireguard,openvpn。此处选 7days
        并调用 parse_server_list 爬取服务器列表页面信息。该列表不是总列表，一页最多列出2个服务器，需要点下一页
        '''
        # server_group_heads_urls = response.xpath('//a[@class="btn btn-primary"]/@href').getall()
        server_group_heads_urls = response.xpath('//a[@class="btn btn-block btn-lg btn-white"]/@href').getall()
        # logging.info(server_group_heads_urls)
        init_server_list_url = self.base_url+server_group_heads_urls[1]
        yield SshServerProviderHostItem({
            'provider_host': 'jagoanssh.com',
            'list_url'     : init_server_list_url
        })
        yield scrapy.Request(init_server_list_url, self.parse_server_list, headers={"referer":response.url})

    def parse_server_list(self, response):
        '''
        ①爬取服务器列表页面信息（一页最多两个服务器），即每个服务器的可用性（available）（完全是数字，不可用为0）、填表页面 url
          调用 parse_server_before_fillingForm 进行填表
        ②爬取下一页服务器列表页面的url
          调用 parse_server_list 继续爬取下一页
        '''
        server_htmls = response.xpath('//div[@class="col-lg-4 col-md"]').getall()
        server_selectors = [Selector(text=h) for h in server_htmls]
        # server_urls = response.xpath('//a[@class="btn btn-primary"]/@href').getall() # ['/?do=create-account&filter=92', '/?do=create-account&filter=93']
        # server_urls = response.xpath('//li[@class="list-group-item"]/a/@href').getall() # ['/?do=create-account&filter=92', '/?do=create-account&filter=93']
        server_urls = [s.xpath('//li[@class="list-group-item"]/a/@href').get() for s in server_selectors]  # ['/?do=create-account&filter=92', '/?do=create-account&filter=93']
        server_urls = [self.base_url+url[1:] for url in server_urls] # ['https://www.jagoanssh.com/?do=create-account&filter=92', 'https://www.jagoanssh.com/?do=create-account&filter=93']
        # server_availables = response.xpath('//span[@class="label label-success"]/text()').getall() # ['0 Available', '0 Available']
        # server_availables = [int(s.split()[0]) for s in server_availables] # [0, 0]
        server_availables = [s.xpath('//li[@class="list-group-item py-2"][5]/text()').get() for s in server_selectors] # ['Remaining: 0 From 20', 'Remaining: ']
        for i in range(len(server_availables)):
            if server_availables[i]!='Remaining: ':
                server_availables[i] = 0    # 0
            else:
                server_availables[i] = int(server_selectors[i].xpath('//span[@class="label label-success"]/text()').get().split()[0])   # 20
        # server_regions = response.xpath('//div[@class="probootstrap-pricing popular"]/h4/text()').getall() # ['SINGAPORE ', 'SINGAPORE ']
        server_regions = [s.xpath('//li[@class="list-group-item py-2"][2]/text()').get() for s in server_selectors] # ['Location: Singapore ', 'Location: Singapore ']
        server_regions = [r[10:].strip() for r in server_regions] # ['Singapore', 'Singapore']
        # server_hosts = response.xpath('//div[@class="probootstrap-pricing popular"]/ul').getall()
        # server_hosts = [scrapy.Selector(text=html).xpath('//li/text()').get() for html in server_hosts] # ['sg1-7.ipservers.xyz', 'sg2-7.ipservers.xyz']
        next_server_list_url = self.base_url+response.xpath('//a[@aria-label="Next"]/@href').get() # 'https://www.jagoanssh.com/?do=v2ray&filter=&page=5'

        if len(server_urls)>0:
            yield scrapy.Request(next_server_list_url, self.parse_server_list, headers={"referer":response.url})

        for i,available in enumerate(server_availables):
            logging.info('++++++++++++ server info ++++++++++++++')
            logging.info(f'region   : {server_regions[i]}')
            # logging.info(f'host     : {server_hosts[i]}')
            logging.info(f'available: {available}')
            logging.info('+++++++++++++++++++++++++++++++++++++++')
            if available>0:
                yield scrapy.Request(
                    server_urls[i], 
                    self.parse_server_before_fillingForm, 
                    headers={"referer":response.url},
                    meta = {
                        'request_interval_secs': self.fillingForm_interval_secs if  GlobalCounter_arr[self.CRAWLED_IDX].show()>0 else 0,
                        'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].count()
                    }  # meta 数据用于给 DeferringDownloaderMiddleware 传参
                )
            else: # available==0
                yield SshServerConfigItem({
                    'region'          : server_regions[i],
                    # 'host'            : server_hosts[i],
                    'error_info'      : 'no available'
                })


    def parse_server_before_fillingForm(self, response):
        ''' 填表以及通过 recaptcha '''
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        logging.info('----已获取recaptcha_res----')
        yield scrapy.FormRequest.from_response(
            response,
            formdata={
                'id': response.url.split('=')[-1],
                'username': getRandStr(12),
                'password': getRandStr(12),
                'g-recaptcha-response': recaptcha_res,
                'createAcc': ''
            },
            callback=self.parse_server_after_fillingForm
        )
        
    def parse_server_after_fillingForm(self, response):
        logging.info('----已进入parse_server_after_fillingForm----')
        ''' 爬取注册账户后服务器的配置信息 '''
        if platform.system() != 'Windows': # windows 没有 time.tzset()，但是 windows 一般时区是正确的，不用设置
            os.environ['TZ']='GMT-8' # 设置成中国所在的东八区时区
            time.tzset()
        def normalize_date(datestr): # 如把 ' 17-07-2022' 标准化成 '2022-07-17'
            return time.strftime("%Y-%m-%d",time.strptime(datestr,"%d-%m-%Y"))
        try:
            # success_info = response.xpath('//div[@class="alert alert-success alert-dismissable"]/text()').getall()
            yield SshServerConfigItem({
                'region'          : response.xpath('//h1/text()').get()[19:].strip(),
                'username'        : response.xpath('//div[@class="alert alert-success alert-dismissable"]/li[2]/span/text()').get().split(': ')[-1].strip(),
                'password'        : response.xpath('//div[@class="alert alert-success alert-dismissable"]/li[3]/span/text()').get().split(': ')[-1].strip(),
                'host'            : response.xpath('//div[@class="alert alert-success alert-dismissable"]/li[1]/span/text()').get().split(': ')[-1].strip(),
                'date_created'    : time.strftime("%Y-%m-%d",time.localtime()), # 这个网址不显示账户的注册时间，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
                'date_expired'    : normalize_date(response.xpath('//div[@class="alert alert-success alert-dismissable"]/li[4]/span/text()').get().split(': ')[-1].strip()),
                # 'max_logins'      : response.xpath('//div[@class="alert alert-danger text-center"]/text()').get().split()[3]
                'max_logins'      : '1'
            })
        except Exception as e:
            try:
                yield SshServerConfigItem({
                    'region'          : response.xpath('//h1/text()').get().split()[-1],
                    'host'            : response.xpath('//table[@class="table table-hover"]/tbody/tr[1]/td/text()').get().strip(),
                    'error_info'      : response.xpath('//div[@class="alert alert-danger alert-dismissable"]/text()[3]').get().strip()
                })
            except Exception as e:
                logging.error(e)
                with open(f'server3_{GlobalCounter.count()}.html', 'wb') as f:
                    f.write(response.body)