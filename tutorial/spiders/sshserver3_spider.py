import scrapy, time, os, asyncio
from utils.common_tools import getRandStr, GlobalCounter, MyCounter, GlobalCounter_arr
from ..items import SshServerProviderHostItem, SshServerConfigItem
from utils.ReCaptcha_Solvers import ReCaptcha_v2_Solver

# scrapy crawl sshservers3
class SSHServers3Spider(scrapy.Spider):
    name = "sshservers3"
    base_url = "https://www.jagoanssh.com/"
    # crawled_server_cnt = MyCounter() # 经实验，不同线程之间不能共享这两个变量，因此考虑使用全局变量 GlobalCounter_arr
    # ommited_server_cnt = MyCounter()
    CRAWLED_IDX = 0 # 这两个是上面两个变量对应转换到 GlobalCounter_arr 中的索引
    OMMITED_IDX = 1
    fillingForm_interval_secs = 60*5+2 # 该网站要求5min后才能创建下一个新用户
    
    custom_settings = {
        # 'DOWNLOAD_DELAY': 5*60+2, 
        # "AUTOTHROTTLE_ENABLED" : True,
        # 'AUTOTHROTTLE_DEBUG': True,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47',
        'ITEM_PIPELINES' : {
            'tutorial.pipelines.SshServerWritingJsonPipeline': 300,
        }
    }

    def start_requests(self):
        list_url = 'https://www.jagoanssh.com/' # 该网站不支持直接输入网址访问，必须从已有页面点击
        yield scrapy.Request(list_url, self.parse)

    def parse(self, response):
        # 爬取服务器组列表页面，该列表有4项可选：3days,7days,vip,ss。此处选 7days
        # 并调用 parse_server_list 爬取服务器列表页面信息。该列表不是总列表，一页最多列出2个服务器，需要点下一页
        server_group_heads_urls = response.xpath('//a[@class="btn btn-primary"]/@href').getall()
        # print(server_group_heads_urls)
        init_server_list_url = self.base_url+server_group_heads_urls[1]
        yield SshServerProviderHostItem({
            'provider_host': 'jagoanssh.com',
            'list_url'     : init_server_list_url
        })
        yield scrapy.Request(init_server_list_url, self.parse_server_list, headers={"referer":response.url})

    def parse_server_list(self, response):
        # ①爬取服务器列表页面信息（一页最多两个服务器），即每个服务器的可用性（available）（完全是数字，不可用为0）、填表页面 url
        #   调用 parse_server_before_fillingForm 进行填表
        # ②爬取下一页服务器列表页面的url
        #   调用 parse_server_list 继续爬取下一页
        # print("in parse_server_list")
        server_urls = response.xpath('//a[@class="btn btn-primary"]/@href').getall() # ['/?do=create-account&filter=92', '/?do=create-account&filter=93']
        server_urls = [self.base_url+url[1:] for url in server_urls] # ['https://www.jagoanssh.com/?do=create-account&filter=92', 'https://www.jagoanssh.com/?do=create-account&filter=93']
        server_availables = response.xpath('//span[@class="label label-success"]/text()').getall() # ['0 Available', '0 Available']
        server_availables = [int(s.split()[0]) for s in server_availables] # [0, 0]
        # print(server_urls)
        # print(server_availables)
        next_server_list_url = self.base_url+response.xpath('//a[@aria-label="Next"]/@href').get()
        # print(next_server_list_url)

        if len(server_urls)>0:
            yield scrapy.Request(next_server_list_url, self.parse_server_list, headers={"referer":response.url})

        for i,available in enumerate(server_availables):
            if available>0:
                # if self.crawled_server_cnt.count()>1:
                if GlobalCounter_arr[self.CRAWLED_IDX].count()>1:
                    print(f'============================================================================================================')
                    # print(f'===========等待{self.fillingForm_interval_secs}s后爬取第{self.crawled_server_cnt.show()}个服务器==============')
                    print(f'===========等待{self.fillingForm_interval_secs}s后爬取第{GlobalCounter_arr[self.CRAWLED_IDX].show()}个服务器==============')
                    print(f'============================================================================================================')
                    asyncio.sleep(self.fillingForm_interval_secs)
                yield scrapy.Request(server_urls[i], self.parse_server_before_fillingForm, headers={"referer":response.url})
                print(f'------------------------------------------------------------------------------------------------------------')
                # print(f'-----------------------------现在已爬取完{self.crawled_server_cnt.show()}个服务器-----------------------------')
                print(f'-----------------------------现在已爬取完{GlobalCounter_arr[self.CRAWLED_IDX].show()}个服务器-----------------------------')
                print(f'------------------------------------------------------------------------------------------------------------')
            else:
                # self.ommited_server_cnt.count()
                GlobalCounter_arr[self.OMMITED_IDX].count()
                print(f'------------------------------------------------------------------------------------------------------------')
                # print(f'-----------------------------现在绕过{self.crawled_server_cnt.show()}个服务器不进行爬取-----------------------------')
                print(f'-----------------------------现在绕过{GlobalCounter_arr[self.OMMITED_IDX].show()}个服务器不进行爬取-----------------------------')
                print(f'------------------------------------------------------------------------------------------------------------')


    def parse_server_before_fillingForm(self, response):
        # 填表以及通过 recaptcha
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        recaptcha_res = ReCaptcha_v2_Solver()(response.url, websiteKey)
        return scrapy.FormRequest.from_response(
            response,
            formdata={
                'id': response.url.split('=')[-1],
                'username': getRandStr(),
                'password': getRandStr(),
                'g-recaptcha-response': recaptcha_res,
                'createAcc': 'Create+Now'
            },
            callback=self.parse_server_after_fillingForm
        )
        
    def parse_server_after_fillingForm(self, response):
        # 爬取注册账户后服务器的配置信息
        # body_strlist = response.xpath('//text()').getall()
        # if len(body_strlist) == 1:
        #     return SshServerConfigItem({
        #         'error_info': body_strlist[0]
        #     })

        os.environ['TZ']='GMT-8' # 设置成中国所在的东八区时区
        time.tzset()
        def normalize_date(datestr): # 如把 ' 17-07-2022' 标准化成 '2022-07-17'
            return time.strftime("%Y-%m-%d",time.strptime(datestr," %d-%m-%Y"))
        try:
            success_info = response.xpath('//div[@class="alert alert-success alert-dismissable"]/text()').getall()
            # print('-------------success_info----------------')
            # print(success_info)
            return SshServerConfigItem({
                'region'          : response.xpath('//h1/text()').get().split()[-1],
                'username'        : success_info[2].split(':')[-1][1:],
                'password'        : success_info[3].split(':')[-1][1:],
                'host'            : success_info[1].split(':')[-1][1:],
                'date_created'    : time.strftime("%Y-%m-%d",time.localtime()), # 这个网址不显示账户的注册时间，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
                'date_expired'    : normalize_date(success_info[4].split(':')[-1]),
                'max_logins'      : response.xpath('//div[@class="alert alert-danger text-center"]/text()').get().split()[3]
            })
        except:
            with open(f'{GlobalCounter.count()}.html', 'wb') as f:
                f.write(response.body)