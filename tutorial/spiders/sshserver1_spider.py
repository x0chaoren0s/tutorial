import scrapy, time
from utils.common_tools import getRandStr
from ..items import SshServerProviderHostItem, SshServerConfigItem

# scrapy crawl sshservers1
class SSHServers1Spider(scrapy.Spider):
    name = "sshservers1"
    custom_settings = {
        'DOWNLOAD_DELAY': 62, # 该网站要求60s后再创建一个新用户
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.47',
        'ITEM_PIPELINES' : {
            'tutorial.pipelines.SshServerWritingJsonPipeline': 300,
        }
    }

    def start_requests(self):
        list_url = 'https://www.mytunneling.com/ssh-server-30' # 仅存储服务器列表页面url
        yield scrapy.Request(list_url, self.parse)

    def parse(self, response): # 仅爬取服务器列表页面，并调用parse_server爬取各服务器的配置
        provider_host = response.css('a.navbar-brand::text').get()
        yield SshServerProviderHostItem({
            'provider_host': provider_host,
            'list_url'     : response.url
        })

        servers_urls = response.css('div.row a::attr(href)').getall() # 完整url
        yield from response.follow_all(servers_urls, self.parse_server_before_fillingForm)

    def parse_server_before_fillingForm(self, response): # 填表注册账户
        serverid = response.css('input').attrib['value']
        return scrapy.FormRequest(
            url='https://www.mytunneling.com/create-account-ssh-30.php',
            formdata={'serverid': serverid, 'username': getRandStr(), 'password': getRandStr()},
            callback=self.parse_server_after_fillingForm
        )
    def parse_server_after_fillingForm(self, response): # 爬取注册账户后服务器的配置信息
        body_strlist = response.xpath('//text()').getall()
        if len(body_strlist) == 1:
            return SshServerConfigItem({
                'error_info': body_strlist[0]
            })

        def normalize_date(datestr): # 如把 05-June-2022 标准化成 2022-06-05
            return time.strftime("%Y-%m-%d",time.strptime(datestr,"%d-%B-%Y"))
        return SshServerConfigItem({
            'username':     body_strlist[1],
            'password':     body_strlist[4].split(':')[1].split()[0],
            'host':         body_strlist[5].split(':')[1].split()[0],
            'date_created': normalize_date(body_strlist[6].split(':')[1].split()[0]),
            'date_expired': normalize_date(body_strlist[7].split(':')[1].split()[0])
        })