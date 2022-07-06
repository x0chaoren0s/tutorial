# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import os, time, json
from .items import SshServerProviderHostItem, SshServerConfigItem


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
        'configs'      : []
    }
    
    def close_spider(self, spider):
        self.create_time = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())
        self.filename = f"{self.create_time}_{self.content_dict['provider_host']}.json"
        self.content_dict['create_time'] = self.create_time
        with open(os.path.join(self.outdir,self.filename), 'w') as f:
            json.dump(self.content_dict, f, indent=4, ensure_ascii=True)

    def process_item(self, item, spider):
        if isinstance(item, SshServerProviderHostItem):
            self.content_dict['provider_host'] = item['provider_host']
            self.content_dict['list_url']      = item['list_url']
        elif isinstance(item, SshServerConfigItem):
            self.content_dict['configs'].append(dict(item))
        