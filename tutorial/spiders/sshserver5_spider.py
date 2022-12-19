import scrapy, time, os, platform
from utils.common_tools import getRandStr, GlobalCounter, GlobalCounter_arr, normalized_local_date, normalize_date
from ..items import SshServerProviderHostItem, SshServerConfigItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

# scrapy crawl sshservers5
class SSHServers5Spider(scrapy.Spider):
    name = "sshservers5"
    base_url = "https://serverssh.net"
    # crawled_server_cnt = MyCounter() # 经实验，不同线程之间不能共享这两个变量，因此考虑使用全局变量 GlobalCounter_arr
    # ommited_server_cnt = MyCounter()
    CRAWLED_IDX = 0 # 这两个是上面两个变量对应转换到 GlobalCounter_arr 中的索引
    OMMITED_IDX = 1
    fillingForm_interval_secs = 60*5+2 # 该网站要求 5 min 后才能创建下一个新用户
    
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
        'CONCURRENT_REQUESTS' : 1 # default 16 最大并发数，该网站要求每次创建用户前后有固定间隔，因此并发数设为1，间隔时间就不用累加设置
    }

    def start_requests(self):
        yield scrapy.Request(self.base_url, self.parse)

    def parse(self, response):
        '''
        爬取服务器组列表页面，该列表有6项可选：3days,7days,30days,openvpn,ss,v2ray。此处选 7days（30days抢不到服务器）
        并调用 parse_server_list 爬取服务器列表页面信息。该列表不是总列表，一页最多列出2个服务器，需要点下一页
        '''
        server_group_heads_urls = response.xpath('//div[@class="col-lg-4 col-md"]//a/@href').getall() # ['/?q=ssh-servers', '/?q=ssh-servers&filter=extra', '/?q=ssh-servers&filter=one-month', '/?q=vpn-servers', '/?q=shadowsocks', '/?q=v2ray']
        # print(server_group_heads_urls)
        init_server_list_url = self.base_url + server_group_heads_urls[1] # 'https://serverssh.net/?q=ssh-servers&filter=extra'
        yield SshServerProviderHostItem({
            'provider_host': 'serverssh.net',
            'list_url'     : init_server_list_url
        })
        yield scrapy.Request(init_server_list_url, self.parse_server_list, headers={"referer":response.url})

    def parse_server_list(self, response):
        '''
        ①爬取服务器列表页面信息（一页最多两个服务器），即每个服务器的可用性（available）（Remaining：数字）、填表页面 url
          调用 parse_server_before_fillingForm 进行填表
        ②爬取下一页服务器列表页面的url
          调用 parse_server_list 继续爬取下一页
        '''
        server_htmls = response.xpath('//div[@class="col-lg-4 col-md"]').getall()
        server_seletors = [scrapy.Selector(text=html) for html in server_htmls]
        server_urls = [s.xpath('//a[@class="btn btn-sm btn-primary hover-translate-y-n3 hover-shadow-lg mb-3"]/@href').get()
            for s in server_seletors] # ['/?q=create-ssh&filter=5', '/?q=create-ssh&filter=6']
        server_urls = [self.base_url+url for url in server_urls] # ['https://serverssh.net/?q=create-ssh&filter=5', 'https://serverssh.net/?q=create-ssh&filter=6']
        server_remainings = [s.xpath('//li[@class="list-group-item py-2"]/text()').getall()[3]
            for s in server_seletors] # ['Remaining: 0 From 15', 'Remaining: '] # 若有服务器可用，则 'Remaining: ' 下面还有一个元素专门显示有多少个
        server_availables = [r=='Remaining: ' for r in server_remainings] # [False, True]
        server_regions = [s.xpath('//li[@class="list-group-item py-2"]/text()').getall()[0]
            for s in server_seletors] # ['Location: Singapore', 'Location: Singapore']
        server_regions = [r.split('Location: ')[1].strip() for r in server_regions] # ['Singapore', 'Singapore']
        server_hosts = [s.xpath('//li[@class="list-group-item py-2"][1]/span/text()').get().strip()
            for s in server_seletors] # ['SGX1', 'SGX2']
        server_hosts = [h.lower()+'.serverssh.net' for h in server_hosts] # ['sgx1.serverssh.net', 'sgx2.serverssh.net']

        next_server_list_btn = response.xpath('//ul[@class="pagination justify-content-center"]/li[last()]')
        if 'disabled' not in next_server_list_btn.xpath('@class').get():
            next_server_list_url = self.base_url + '/' + next_server_list_btn.xpath('a/@href').get()
            yield scrapy.Request(next_server_list_url, self.parse_server_list, headers={"referer":response.url})

        for i,available in enumerate(server_availables):
            print('++++++++++++ server info ++++++++++++++')
            print(f'region   : {server_regions[i]}')
            print(f'host     : {server_hosts[i]}')
            print(f'available: {available}')
            print('+++++++++++++++++++++++++++++++++++++++')
            if available:
                yield scrapy.Request(
                    server_urls[i], 
                    self.parse_server_before_fillingForm, 
                    headers={"referer":response.url},
                    meta = {
                        'region': server_regions[i], # 该网站注册成功页面没有服务器的地区信息，因此在这里传参过去
                        'request_interval_secs': self.fillingForm_interval_secs,  # 用于给 DeferringDownloaderMiddleware 传参
                        'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].count() # 用于给 DeferringDownloaderMiddleware 传参
                    }  
                )
            else: # available == False
                yield SshServerConfigItem({
                    'region'          : server_regions[i],
                    'host'            : server_hosts[i],
                    'error_info'      : 'no available'
                })


    def parse_server_before_fillingForm(self, response):
        ''' 填表以及通过 recaptcha '''
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        yield scrapy.FormRequest.from_response(
            response,
            formdata={
                'id': response.url.split('=')[-1],
                'username': getRandStr(12),
                'password': getRandStr(12),
                'g-recaptcha-response': recaptcha_res,
                'createAcc': ''
            },
            callback=self.parse_server_after_fillingForm,
            meta = {
                'region': response.meta['region'], # 该网站注册成功页面没有服务器的地区信息，因此从 parse_server_list 传参过去
            }
        )
        
    def parse_server_after_fillingForm(self, response):
        ''' 爬取注册账户后服务器的配置信息 '''
        if platform.system() != 'Windows': # windows 没有 time.tzset()，但是 windows 一般时区是正确的，不用设置
            os.environ['TZ']='GMT-8' # 设置成中国所在的东八区时区
            time.tzset()
        try:
            success_info = response.xpath('//li[@class="list-group-item py-3"]/font/b/text()').getall()
            print(success_info)
            yield SshServerConfigItem({
                'region'          : response.meta['region'],
                'username'        : success_info[1].split(':')[-1].strip(),
                'password'        : success_info[2].split(':')[-1].strip(),
                'host'            : success_info[0].split(':')[-1].strip(),
                'date_created'    : normalized_local_date(), # 这个网址不显示账户的注册时间，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
                'date_expired'    : normalize_date(success_info[3].split(':')[-1].strip(), '%d-%m-%Y'), # 该网站日期格式 04-08-2022
                'max_logins'      : '1' # 该网站 3days 最大设备数为 2, 7days 最大设备数为 1
            })
        except Exception as e:
            try:
                yield SshServerConfigItem({
                    'region'          : response.xpath('//meta[@name="description"]/@content').get().split('Free Premium SSH Tunnel 7 Days Servers ')[-1].strip(),
                    'host'            : response.xpath('//table/tbody/tr[1]/td/text()').get().strip(),
                    'error_info'      : response.xpath('//div[@class="alert alert-danger alert-dismissable"]/text()[3]').get().strip()
                })
            except Exception as e:
                print(e)
                with open(f'server5_{GlobalCounter.count()}.html', 'wb') as f:
                    f.write(response.body)