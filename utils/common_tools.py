import random, string, time
from typing import Iterable

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

def normalize_date(datestr: str, date_pattern: 'str | Iterable[str]', normalizing_pattern: str="%Y-%m-%d") -> str:
    """
    #### 可将网站给的时间日期格式转换成本项目采用的标准日期格式 "%Y-%m-%d"
    如把 ' 17-07-2022' 标准化成 '2022-07-17'

    %a Locale’s abbreviated weekday name.

    %A Locale’s full weekday name.

    %b Locale’s abbreviated month name.

    %B Locale’s full month name.

    %c Locale’s appropriate date and time representation.

    %d Day of the month as a decimal number [01,31].

    %H Hour (24-hour clock) as a decimal number [00,23].

    %I Hour (12-hour clock) as a decimal number [01,12].

    %j Day of the year as a decimal number [001,366].

    %m Month as a decimal number [01,12].

    %M Minute as a decimal number [00,59].

    %p Locale’s equivalent of either AM or PM.

    %S Second as a decimal number [00,61].

    %U Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0.

    %w Weekday as a decimal number [0(Sunday),6].

    %W Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0.

    %x Locale’s appropriate date representation.

    %X Locale’s appropriate time representation.

    %y Year without century as a decimal number [00,99].

    %Y Year with century as a decimal number.

    %z Time zone offset indicating a positive or negative time difference from UTC/GMT of the form +HHMM or -HHMM, where H represents decimal hour digits and M represents decimal minute digits [-23:59, +23:59]. 1

    %Z Time zone name (no characters if no time zone exists). Deprecated. 1

    %% A literal '%' character.
    """
    for pattern in [date_pattern] if isinstance(date_pattern, str) else date_pattern:
        try:
            return time.strftime(normalizing_pattern, time.strptime(datestr,pattern))
        except:
            pass
    raise ValueError(f"time data '{datestr}' does not match any format in {[date_pattern] if isinstance(date_pattern, str) else date_pattern}")

def normalized_local_date() -> str:
    '''
    #### 输出标准化的当前日期，如 '2022-07-28'
    可用于不显示账户的注册时间的网站，所以自己填。但其实不太准确，因为不知道网站的显示的到期时间是用什么时区
    '''
    return time.strftime("%Y-%m-%d",time.localtime())

if __name__ == '__main__':
    # print(getRandStr())
    # print(GlobalCounter.show())
    # print(GlobalCounter.count())
    # print(GlobalCounter.show())
    # print(GlobalCounter.count(3))
    # print(normalized_local_date())
    print(normalize_date(' 17-07-2022'," %d-%m-%Y"))
    print(normalize_date('2023-03-28 / 21:07:04',"%Y-%m-%d / %H:%M:%S"))
    print(normalize_date('2023-03-28',["%Y-%m-%d", "%Y-%m-%d / %H:%M:%S"]))
