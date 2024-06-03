import time

import requests
import json
import datetime
import random

def send_wx_msg(content):
    """艾特全部，并发送指定信息"""
    # wx_urls = ['https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=78b63b8d-837b-4ae1-a2b5-39e781f5eaca', ' https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=979c6e29-8596-43b3-a8f1-bad5bdbf4927', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=688f7a33-dd0e-4658-a688-1451a4ea5b70']
    # oneshot
    # wx_urls = ['https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=629df2e2-f227-40b3-b82f-8c04feef5cbb', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=89069125-3101-4188-85d9-497b6c0e107a', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=2cc42c3a-97e6-45b8-9d51-186146efd262']
    # 康kang
    wx_urls = ['https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9ff3e5e4-0c68-4859-b9eb-cc557bf17e84', 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4ea7dc92-dc78-407d-bcb3-08241050169e']
    data = json.dumps({"msgtype": "text", "text": {"content": content, "mentioned_list":["@all"]}})
    r = requests.post(random.choice(wx_urls), data, auth=('Content-Type', 'application/json'))
    print(r.json)
    return r


def loop_send_wx_msg(content):
    index = 0
    while True:
        index += 1
        resp = send_wx_msg(content)
        # print(help(resp))
        if resp.status_code == 200:
            break
        time.sleep(3)
        if index >= 3:
            break


def get_current_time():
    """获取当前时间，当前时分秒"""
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    hour = datetime.datetime.now().strftime("%H")
    mm = datetime.datetime.now().strftime("%M")
    ss = datetime.datetime.now().strftime("%S")
    return now_time, hour, mm, ss


def sleep_time(hour = 0, minute = 0, sec = 0):
    """返回总共秒数"""
    return hour * 3600 + minute * 60 + sec


def get_trader_info():
    proxy = {'http': 'http://127.0.0.1:7890',
             'https': 'http://127.0.0.1:7890',}
    traderwagon_url = "https://www.traderwagon.com/v1/public/social-trading/lead-portfolio/get-position-info/4451"
    proxy = None
    rep = requests.get(traderwagon_url, proxies=proxy)
    # print(rep.json()['data'])
    return rep.json()['data']


if __name__ == '__main__':
    webhook_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=688f7a33-dd0e-4658-a688-1451a4ea5b70"
    content = "你好"
    send_wx_msg(content)