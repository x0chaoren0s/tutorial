import scrapy
from utils.common_tools import getRandStr, normalize_date, normalized_local_date, GlobalCounter
from ..items import SshServerProviderHostItem, SshServerConfigItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

# scrapy crawl sshserver7
class SSHServers7Spider(scrapy.Spider):
    name = "sshserver7"
    base_url = "https://akunssh.net/"
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
        list_url = 'https://akunssh.net/ssh-server-7?page=1' # 存储4个服务器入口，以及page跳转按钮【1】【2】，没有下一页按钮
        yield scrapy.Request(list_url, self.parse, headers={"referer":self.base_url})

    def parse(self, response):
        '''
        判断当前页是否合法，若是则
        ①爬取下一页
        ②爬取本页面内各服务器信息，对还有容量的服务器（available）
        调用 parse_server_before_fillingForm 进行填表
        '''
        server_strs = response.xpath('//div[@class="col-lg-3 mb-5"]').getall() # 是一个str的list
        # server_strs = list(set(server_strs)) # 这个网站的页面可能有重复的服务器，用set去重
        server_selectors = [scrapy.Selector(text=svr) for svr in server_strs] # str 转回 selector
        
        if len(server_selectors) < 1:
            yield SshServerProviderHostItem({
                'provider_host': 'akunssh.net',
                'list_url'     : 'https://akunssh.net/ssh-server-7?page=1'
            })
            return
        
        now_list_url = response.url
        now_list_idx = int(now_list_url.split('=')[-1])
        list_url_base = now_list_url.split('=')[0] + '='
        next_list_url = list_url_base + f'{now_list_idx+1}'
        yield scrapy.Request(next_list_url, self.parse, headers={"referer":response.url})

        server_hosts = [s.xpath('//li[@class="pricing-list-item"][1]/text()').get().split('Host ')[-1].strip() for s in server_selectors]
        server_regions = [s.xpath('//li[@class="pricing-list-item"][4]/text()').get().split('Location ')[-1].strip() for s in server_selectors]
        server_availables = [s.xpath('//span[@class="badge badge-pill badge-primary"]/text()').get() is not None and
            s.xpath('//span[@class="badge badge-pill badge-primary"]/text()').get() != '0'
            for s in server_selectors] # [False, False, True, True]
        server_urls = [s.xpath('//a[@class="btn btn-primary btn-marketing rounded-pill"]/@href').get() for s in server_selectors] # ['https://akunssh.net/create/ssh-7-id2-account',..]

        for avai,url,host,region in zip(server_availables, server_urls, server_hosts, server_regions):
            if avai: # avalaible: True
                yield scrapy.Request(
                    url, 
                    self.parse_server_before_fillingForm, 
                    headers={"referer":response.url},
                    meta = {
                        'region'    : region, # 该网站注册成功页面没有服务器的地区信息，因此在这里传参过去
                        'host'      : host      # 用于recaptcha求错的时候记录到输出文件
                        # 'request_interval_secs': self.fillingForm_interval_secs,  # 用于给 DeferringDownloaderMiddleware 传参
                        # 'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].show() # 用于给 DeferringDownloaderMiddleware 传参
                    }  
                )
            else: # avalaible: False
                yield SshServerConfigItem({
                    'region'          : region,
                    'host'            : host,
                    'error_info'      : 'no available'
                })


    def parse_server_before_fillingForm(self, response):
        ''' 填表以及通过 recaptcha '''
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        yield scrapy.FormRequest(
            'https://akunssh.net/add/ssh',
            formdata ={
                'csrf_test_name': response.xpath('//input[@name="csrf_test_name"]/@value').get(),
                'slug':           response.xpath('//input[@name="slug"]/@value').get(),
                'username': getRandStr(12),
                'password': getRandStr(12),
                'g-recaptcha-response': recaptcha_res,
                'submit': ''
            },
            headers={"referer":response.url},
            callback=self.parse_server_after_fillingForm,
            meta = {
                'region'    : response.meta['region'], # 该网站注册成功页面没有服务器的地区信息，因此在这里传参过去
                'host'      : response.meta['host']      # 用于recaptcha求错的时候记录到输出文件
                # 'request_interval_secs': self.fillingForm_interval_secs,  # 用于给 DeferringDownloaderMiddleware 传参
                # 'cnt_crawled': GlobalCounter_arr[self.CRAWLED_IDX].show() # 用于给 DeferringDownloaderMiddleware 传参
            } 
        )
        
    def parse_server_after_fillingForm(self, response):
        ''' 爬取注册账户后服务器的配置信息 '''
        if response.text.find('Captcha not valid.')!=-1:
            yield SshServerConfigItem({
                'region'          : response.meta['region'],
                'host'            : response.meta['host'],
                'error_info'      : 'Captcha not valid.'
            })
        elif response.text.find('Oops server did not respond please try another server..!')!=-1:
            yield SshServerConfigItem({
                'region'          : response.meta['region'],
                'host'            : response.meta['host'],
                'error_info'      : 'server did not respond'
            })
        else:
            try:
                yield SshServerConfigItem({
                    'region'          : response.meta['region'],
                    'username'        : response.xpath('//div[@class="alert alert-card alert-success"]/text()[6]').get().strip(),
                    'password'        : response.xpath('//div[@class="alert alert-card alert-success"]/text()[8]').get().strip(),
                    'host'            : response.xpath('//div[@class="alert alert-card alert-success"]/text()[4]').get().strip(),
                    'port'            : response.xpath('//div[@class="alert alert-card alert-success"]/text()[10]').get().strip(),
                    'date_created'    : normalize_date(response.xpath('//div[@class="alert alert-card alert-success"]/text()[26]').get().strip(), '%d-%b-%Y'),
                    'date_expired'    : normalize_date(response.xpath('//div[@class="alert alert-card alert-success"]/text()[28]').get().strip(), '%d-%b-%Y'),
                    'max_logins'      : '99' # 该网站似乎没有限制登录设备数量
                })
            except:
                with open(f'server7_{GlobalCounter.count()}.html', 'wb') as f:
                    f.write(response.body)