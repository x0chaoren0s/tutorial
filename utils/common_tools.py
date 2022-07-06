import random, string

# https://www.cnblogs.com/yaner2018/p/11269847.html
#数字+字母+符号
def getRandStr(strLen = -1):
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

if __name__ == '__main__':
    print(getRandStr())