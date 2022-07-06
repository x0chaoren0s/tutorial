import scrapy, os, shutil

# scrapy crawl novel -a menu="http://www.dsyqxs.com/71890/"
class NovelSpider(scrapy.Spider):
    name = "novel"
    def start_requests(self):
        menu_url = 'http://www.dsyqxs.com/71890/' # 仅存储目录页面url
        menu = getattr(self, 'menu', None) # 可命令行传参指定menu_url
        if menu:
            menu_url = menu
        yield scrapy.Request(menu_url, self.parse)

    def parse(self, response): # 仅爬取目录页面，并调用parse_chapter爬取各章节页面
        novel_title = response.css('div.btitle h1::text').get()
        author = response.css('div.btitle em::text').get()
        author = author.split('：')[1]
        self.project_name = novel_title+'（'+author+'）'

        chpts = response.css('dl.chapterlist')
        chpts_urls = chpts.css('dd a::attr(href)').getall()
        chpts_urls = [url.split('/')[2] for url in chpts_urls]
        self.url2id = dict() # 保存章节网址的实际序号，以确保异步io保存的章节序号正确
        for (id,url) in enumerate(chpts_urls):
            self.url2id[url]=id

        self.outdir = os.path.join('results',self.project_name) # 小说存放位置
        shutil.rmtree(self.outdir, ignore_errors=True)
        os.makedirs(self.outdir, exist_ok=False)
        yield from response.follow_all(chpts_urls, self.parse_chapter)

    def parse_chapter(self, response): # 仅爬取特定章节页面
        url = response.url.split('/')[-1]
        id = self.url2id[url]
        chapter_title = f'{id}、'+response.css('h1::text').get().split()[0]
        filename = chapter_title+'.txt'
        
        content = response.css('div[id="BookText"]')
        content_lines = content.css('p::text').getall()
        content_lines = [line+'\n\n' for line in content_lines]
        
        with open(os.path.join(self.outdir,filename), 'w', encoding='utf8') as f:
            f.writelines(content_lines)