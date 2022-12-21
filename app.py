import os, subprocess, json
import streamlit as st

st.header('spider')

spider_list = [file.split('_spider.py')[0] 
                for file in os.listdir('tutorial/spiders') 
                if file.endswith('_spider.py')]

spider = st.selectbox('选择一个爬虫', spider_list)

# crawled = False
# json_path = None
def crawl(spider):
    # global crawled, json_path
    # cwd = r'C:\Users\60490\Desktop\tutorial'
    cwd = '.'
    json_path=subprocess.Popen(
        # 'D:/ProgramData/Anaconda3/envs/spider/python.exe -m scrapy crawl sshservers3', 
        f'python -m scrapy crawl {spider}', 
        stdout=subprocess.PIPE, shell=True, text=True, cwd=cwd, 
        # stderr=subprocess.STDOUT
        ).stdout.read().strip()
    json_path = os.path.join(cwd, json_path)
    st.session_state['json_path'] = json_path
    # crawled = True

    # st.write(json_path)

    # with open(json_path, 'r') as fin:
    #     json_dict = json.load(fin)

    # st.write(json_dict)

st.button('开始爬取', on_click=crawl, kwargs={'spider':spider})


config_list = [file for file in os.listdir('momomo2') if file.endswith('.conf')]
config = st.selectbox('选择要保存到的配置', config_list)
if st.button('显示新的连接'):
    json_path = st.session_state['json_path']
    st.write(json_path)

    with open(json_path, 'r') as fin:
        json_dict = json.load(fin)

    st.write(json_dict)
