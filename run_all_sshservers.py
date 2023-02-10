'''
https://docs.scrapy.org/en/latest/topics/practices.html#running-multiple-spiders-in-the-same-process
'''

# import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings)

    spider_names_set = {'sshserver2','sshserver3','sshserver5','sshserver6','sshserver7'}

    [process.crawl(spider_name) for spider_name in spider_names_set]
    process.start() # the script will block here until all crawling jobs are finished