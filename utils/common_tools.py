import random, string

# https://www.cnblogs.com/yaner2018/p/11269847.html
#数字+字母+符号
def getRandStr(strLen = -1):
    ''' strLen：随机字符串的长度，默认为 -1，代表闭区间 [4,12] 内的随机长度 '''
    if strLen == -1:
        strLen = random.randint(4,12)
    l = []
    #sample = '0123456789abcdefghijklmnopqrstuvwxyz!@#$%^&*()-+=.'
    sample = random.sample(string.ascii_letters + string.digits, 62)## 从a-zA-Z0-9生成指定数量的随机字符： list类型
    # sample = sample + list('!@#$%^&*()-+=.')#原基础上加入一些符号元素
    for i in range(strLen):
        char = random.choice(sample)#从sample中选择一个字符
        l.append(char)
    return ''.join(l)#返回字符串

class MyCounter:
    ''' 自动计数器 '''
    def __init__(self, begin: int = 0) -> None:
        ''' 从 begin 开始计数 '''
        self.begin = begin
        self.accum = self.begin # 累计计数值

    def show(self):
        ''' 返回当前累计计数值 '''
        return self.accum

    def count(self, unit: int = 1) -> int:
        ''' 增加计数 unit 个单位，并返回当前累计计数值 '''
        self.accum += unit
        return self.show()
GlobalCounter = MyCounter()
GlobalCounter_arr = [MyCounter() for _ in range(100)]

if __name__ == '__main__':
    # print(getRandStr())
    print(GlobalCounter.show())
    print(GlobalCounter.count())
    print(GlobalCounter.show())
    print(GlobalCounter.count(3))
