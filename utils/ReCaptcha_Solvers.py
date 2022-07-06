# https://yescaptcha.atlassian.net/wiki/spaces/YESCAPTCHA/pages/4587548/Python+DEMO+requests+requests+demo.py

import time, requests


class ReCaptcha_v2_Solver:
    def __init__(
        self,
        clientKey = "ddd1cf72d9955a0e8ca7d05597fea5eb1dce33de5331", # clientKey：在个人中心获取
        sleep_sec = 3, # 循环请求识别结果，sleep_sec 秒请求一次
        max_sec = 120  # 最多等待 max_sec 秒
    ) -> None:
        self.clientKey = clientKey
        self.sleep_sec = sleep_sec
        self.max_sec = max_sec
        self.task_type = "NoCaptchaTaskProxyless"
    
    def _create_task(self, websiteURL, websiteKey) -> str:
        """ 
        第一步，创建验证码任务 
        :param 
        :return taskId : string 创建成功的任务ID
        """
        url = "https://api.yescaptcha.com/createTask"
        data = {
            "clientKey": self.clientKey,
            "task": {
                "websiteURL": websiteURL,
                "websiteKey": websiteKey,
                "type": self.task_type
            }
        }
        try:
            # 发送JSON格式的数据
            result = requests.post(url, json=data, verify=False).json()
            taskId = result.get('taskId')
            if taskId is not None:
                return taskId
            print(result)
            
        except Exception as e:
            print(e)


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
                result = requests.post(url, json=data, verify=False).json()
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