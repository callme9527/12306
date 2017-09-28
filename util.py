# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/9/18 17:20'
import cPickle as pickle
import requests
import re
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# 禁用安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def get_station_code():
    try:
        with open('station.txt', 'rb') as f:
            stas_dic = pickle.load(f)
            if stas_dic: return stas_dic
    except: pass
    url = 'https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=1.9025'
    res = requests.get(url, verify=False)
    con = res.content
    stas_str = re.search("='(.*?)';", con, re.S).group(1)
    stas_lis = stas_str.split('@')[1:]
    stas_dic = {}
    for sta in stas_lis:
        items = sta.split('|')
        cn_name = items[1]
        num = items[-1]
        en_name = items[-2]
        code = items[2]
        key = (cn_name, en_name)
        val = (code, num)
        stas_dic[key] = val
    with open('station.txt', 'wb') as f:
        pickle.dump(stas_dic, f)
    return stas_dic


def req_get(url, headers, session=None):
    if session:
        res = session.get(url, headers=headers, verify=False, timeout=5)
    else:
        res = requests.get(url, headers=headers, verify=False, timeout=5)
    if res.status_code != 200: return ''
    return res.content


def req_post(url, headers, data, session=None):
    if session:
        res = session.post(url, headers=headers, data=data, verify=False, timeout=5)
    else:
        res = requests.post(url, headers=headers, data=data, verify=False, timeout=5)
    if res.status_code != 200: return ''
    return res.content


class PinError(Exception): pass


class CheckError(Exception): pass


class LoginError(Exception): pass


class AuthError(Exception): pass


class QueryError(Exception): pass


# 输出车次，时间，座次等信息
def show(query):
    line_sep = '-'*99
    index = 0
    for k, v in query.items():
        print line_sep
        print u'从'+k[0].split('.')[1]+u'到'+k[1].split('.')[1]+'   '+k[2]
        print line_sep
        for tic_info in v:
            index += 1
            print str(index)+'. '+tic_info
            print line_sep



