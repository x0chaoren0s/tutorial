# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os, time, json, platform, logging
from .items import SshServerProviderHostItem, SshServerConfigItem, Host2IpItem


class TutorialPipeline:
    def process_item(self, item, spider):
        return item

class SshServerWritingJsonPipeline:
    outdir = 'results/sshservers'
    create_time = ''
    filename = ''
    content_dict = {
        'provider_host': '',
        'list_url'     : '',
        'create_time'  : '',
        'configs'      : [],
        'host2ip'    : dict()
    }
    
    def close_spider(self, spider):
        self._replace_host_2_ip()
        if platform.system() != 'Windows': # windows 没有 time.tzset()，但是 windows 一般时区是正确的，不用设置
            os.environ['TZ']='GMT-8' # 设置成中国所在的东八区时区
            time.tzset()
        self.create_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        self.filename = f"{self.create_time}_{self.content_dict['provider_host']}.json"
        self.content_dict['create_time'] = self.create_time
        os.makedirs(self.outdir, exist_ok=True)
        json_path = os.path.join(self.outdir,self.filename)
        with open(json_path, 'w') as f:
            json.dump(self.content_dict, f, indent=4, ensure_ascii=True)
        print(json_path)

    def process_item(self, item, spider):
        # print(item)
        if isinstance(item, SshServerProviderHostItem):
            self.content_dict['provider_host'] = item['provider_host']
            self.content_dict['list_url']      = item['list_url']
        elif isinstance(item, SshServerConfigItem):
            if 'error_info' not in item:
                if 'port' not in item:
                    item['port'] = '22'
                item['glider_config'] = f"forward=ssh://{item['username']}:{item['password']}@{item['host']}:{item['port']}"
                item['date_span'] = f"# {item['date_created']} - {item['date_expired']}"
            self.content_dict['configs'].append(dict(item))
        elif isinstance(item, Host2IpItem):
            host, ip = item['host'], item['ip']
            self.content_dict['host2ip'][host] = ip
    
    def _replace_host_2_ip(self):
        ''' 有的网站其 host 不能用，而要使用 ip，如 www.vpnjantit.com 。该函数对没有 host2ip 信息的 host 不产生作用 '''
        for config in self.content_dict['configs']:
            if 'error_info' in config:
                continue
            if 'ip' in config:
                continue
            if config['host'] in self.content_dict['host2ip']:
                config['ip'] = self.content_dict['host2ip'][config['host']]
                config['glider_config'] = f"forward=ssh://{config['username']}:{config['password']}@{config['ip']}:{config['port']}"
