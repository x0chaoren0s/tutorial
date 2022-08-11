# https://yescaptcha.atlassian.net/wiki/spaces/YESCAPTCHA/pages/4587548/Python+DEMO+requests+requests+demo.py

import time, requests, scrapy


class UnfinishSpider(scrapy.Spider):
    name = "UnfinishSpider"

    clientKey = "ddd1cf72d9955a0e8ca7d05597fea5eb1dce33de5331", # clientKey：在个人中心获取
    sleep_sec = 3, # 循环请求识别结果，sleep_sec 秒请求一次
    max_sec = 120  # 最多等待 max_sec 秒
    task_type = "NoCaptchaTaskProxyless"

    def start_requests(self):
        pass

    def parse(self, response):
        pass
    
    def unfinished_create_task(self, response, websiteURL, websiteKey):
        """ 
        第一步，创建验证码任务   把下面的代码插入到爬虫体中
        :websiteURL 和 websiteURL 需要现场提取
        :return taskId : string 创建成功的任务ID
        """
        # 可能是这样的，也可能要根据实际情况现场改
        websiteKey = response.xpath('//div[@class="g-recaptcha"]/@data-sitekey').get()
        websiteURL = response.url

        # 下面是调用 yesCaptcha 接口，应该不用改
        url = "https://api.yescaptcha.com/createTask"
        data = {
            "clientKey": self.clientKey,
            "task": {
                "websiteURL": websiteURL,
                "websiteKey": websiteKey,
                "type": self.task_type
            }
        }
        yield scrapy.FormRequest(url, formdata=data)


    def solve(self, websiteURL, websiteKey) -> str:
        """ 
        第二步：使用taskId获取response 
        :param taskID: string
        :return gRecaptchaResponse: string 识别结果
        """
        taskID = self._create_task(websiteURL, websiteKey)
        
        # 循环请求识别结果，sleep_sec 秒请求一次
        times = 0
        while times < self.max_sec:
            try:
                url = f"https://api.yescaptcha.com/getTaskResult"
                data = {
                    "clientKey": self.clientKey,
                    "taskId": taskID
                }
                # result = requests.post(url, json=data, verify=False).json()
                result = requests.post(url, json=data).json()
                solution = result.get('solution', {})
                if solution:
                    gRecaptchaResponse = solution.get('gRecaptchaResponse')
                    if gRecaptchaResponse:
                        return gRecaptchaResponse
                print(result)
            except Exception as e:
                print(e)

            times += self.sleep_sec
            time.sleep(self.sleep_sec)
        
    def __call__(self, websiteURL, websiteKey) -> str:
        return self.solve(websiteURL, websiteKey)