'''
https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process
'''

# import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import os
from multiprocessing.pool import Pool

def run_single_spider(spider_name):
    os.system(f'python -m scrapy crawl {spider_name}')
if __name__ == '__main__':
    settings = get_project_settings()

    spider_names_set = {'sshserver2','sshserver3','sshserver4','sshserver5','sshserver7'}
    # 2:vpnhack.com, 3:www.jagoanssh.com, 4:www.vpnjantit.com, 5:serverssh.net, 6:sshstores.net, 7:akunssh.net

    # 以下两种方案都会把所有服务商的信息累计到最后一个json文件中

    # process = CrawlerProcess(settings)
    # [process.crawl(spider_name) for spider_name in spider_names_set]
    # process.start() # the script will block here until all crawling jobs are finished

    # processes = [CrawlerProcess(settings)] * len(spider_names_set)
    # [process.crawl(spider_name) for process,spider_name in zip(processes,spider_names_set)]
    # [process.start() for process in processes]
    # [process.join() for process in processes]



    # [os.system(f'python -m scrapy crawl {spider_name}') for spider_name in spider_names_set] # 非并发
    with Pool(len(spider_names_set)) as p:   # 并发
        p.map(run_single_spider, spider_names_set)
    