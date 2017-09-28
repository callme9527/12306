# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/9/18 14:14'
import cPickle as pickle
import requests
import json
import time
import sys
import re

from PIL import Image
from urllib import unquote
from random import random
from util import get_station_code, req_get, req_post, show, PinError, LoginError, CheckError, AuthError, QueryError

reload(sys)
sys.setdefaultencoding('utf-8')


class Ticket(object):
    site_code = {
        u'硬座': '1',
        u'软座': '2',
        u'硬卧': '3',
        u'软卧': '4',
        u'高级软卧': '6',
        u'商务座': '9',
        u'一等座': 'M',
        u'二等座': 'O',
        u'动卧': 'F'
    }
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Host': 'kyfw.12306.cn'
        }
        self.query_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0',
            'Cookie': 'RAIL_DEVICEID=KlDyf1bOiej0aWG8h8pKGStQ2ZTXYLNJr2HXlNVZt6NrztWiolZ37_sDhrtCq2mTIH-f_CGEbUYlF4VJLmlZbV1nBiFxrhnDIRhLiaKuvQf6Mwh5qsMm-2NGkzpRBE-XdWJ_4AqVNz7Vv9-Lf5RzxIA4rQpmJWsi;'
        }
        self.pin_url='https://kyfw.12306.cn/passport/captcha/captcha-image?login_site=E&module=login&rand=sjrand&%.17f'
        self.check_pin_url = 'https://kyfw.12306.cn/passport/captcha/captcha-check'
        self.login_url = 'https://kyfw.12306.cn/passport/web/login'
        self.auth1_url = 'https://kyfw.12306.cn/passport/web/auth/uamtk'
        self.auth2_url = 'https://kyfw.12306.cn/otn/uamauthclient'
        self.left_tic_index = 'https://kyfw.12306.cn/otn/leftTicket/init'
        self.left_tic_url = 'https://kyfw.12306.cn/otn/leftTicket/queryX?leftTicketDTO.train_date=%s' \
                            '&leftTicketDTO.from_station=%s&leftTicketDTO.to_station=%s&purpose_codes=ADULT'
        self.price_url = 'https://kyfw.12306.cn/otn/leftTicket/queryTicketPrice?train_no=%s' \
                         '&from_station_no=%s&to_station_no=%s&seat_types=%s&train_date=%s'
        self.check_user_url = 'https://kyfw.12306.cn/otn/login/checkUser'
        self.submit_order_url = 'https://kyfw.12306.cn/otn/leftTicket/submitOrderRequest'
        self.all_query = {}
        self.all_price_arg = []
        self.all_order_arg = []
        self.session = requests.Session()
        self.login_retry_times = 1
        self.login_time = 0

    # login process
    def get_pin(self):
        pin_url = self.pin_url % random()
        # print 'pin_url:'+pin_url
        res = req_get(pin_url, self.headers, self.session)
        if not res: raise PinError
        with open('pin.png', 'wb') as f:
            f.write(res)
        img = Image.open('pin.png')
        img.show()
        # print u'get pin to pin.png.'
        # print 'getpin后的cookies:'+str(self.session.cookies.get_dict())

    def check_pin(self, indexs):
        options = [['44', '37'], ['110', '42'], ['183', '38'], ['257', '43'],
                   ['32', '111'], ['111', '111'], ['194', '118'], ['257', '124']]
        answer = []
        for index in indexs:
            answer.extend(options[int(index)-1])
        answer = ','.join(answer)
        print 'answer:'+answer
        data = {
            'answer': answer,
            'login_site': 'E',
            'rand': 'sjrand'
        }
        res = req_post(self.check_pin_url, self.headers, data, self.session)
        print res
        if not res or u'成功' not in res: raise CheckError

    def login(self, user, pwd):
        data = {
            'appid': 'otn',
            'password': pwd,
            'username': user
        }
        res = req_post(self.login_url, self.headers, data, self.session)
        if not res or u'成功' not in res: raise LoginError

    def auth1(self):
        data = {
            'appid': 'otn'
        }
        res = req_post(self.auth1_url, self.headers, data, self.session)
        if not res or u'通过' not in res: raise AuthError
        self.tk = json.loads(res).get('newapptk', '')

    def auth2(self):
        data = {
            'tk': self.tk
        }
        res = req_post(self.auth2_url, self.headers, data, self.session)
        if not res or u'通过' not in res: raise AuthError

    def get_cookie(self):
        try:
            print u'开始登陆'
            self.get_pin()
            while 1:
                indexs = raw_input(u'input indexs of pics you want click(eg:1 2 3):')
                indexs = re.split('[ |,|、]', indexs)
                print indexs
                indexs = [index for index in indexs if index.isdigit() and 0 < int(index) < 9]
                if not indexs:
                    print u'what the fuck you write'
                    continue
                self.check_pin(indexs)
                user = raw_input('input username:')
                pwd = raw_input('input password:')
                self.login(user, pwd)
                self.auth1()
                self.auth2()
                print u'登陆成功'
                self.login_time = time.time()
                self.login_retry_times = 1
                break
        except:
            if self.login_retry_times > 4:
                print u'shit, u r a b ch!'
                sys.exit()
            self.login_retry_times += 1
            self.get_cookie()

    def check_user(self):
        res = req_post(self.check_user_url, self.headers, {'_json_att': ''}, self.session)
        print str(json.loads(res).get('data', ''))
        return json.loads(res)['data']['flag']

    def _submit_order(self, index):
        order_arg = self.now_order_arg[int(index) - 1]
        print order_arg
        data = {
            'back_train_date': order_arg[3],
            'purpose_codes': 'ADULT',
            'query_from_station_name': order_arg[1].split('.')[-1].strip(),
            'query_to_station_name': order_arg[2].split('.')[-1].strip(),
            'secretStr': unquote(order_arg[0]),
            'tour_flag': 'dc',
            'train_date': order_arg[3],
            'undefined': ''
        }
        cont = req_post(self.submit_order_url, self.headers, data, self.session)
        print cont
        if 'N' in str(json.loads(cont).get('data', '')):
            return True
        return False

    def get_users(self, token):
        url = 'https://kyfw.12306.cn/otn/confirmPassenger/getPassengerDTOs'
        data = {
            'REPEAT_SUBMIT_TOKEN': token,
            '_json_att': ''
        }
        cont = req_post(url, self.headers, data, self.session)
        if not cont: return
        self.users = json.loads(cont)['data']['normal_passengers']

    def query(self):
        self.now_query = {}
        self.now_price_arg = []
        self.now_order_arg = []
        from_city = raw_input('input the from city(eg:bj or 北京): '.decode('utf-8'))
        city_option = []
        city_codes = {}
        index = 1
        sta_dict = get_station_code()
        # print sta_dict
        for k, v in sta_dict.items():
            if from_city in k:
                city_option.append(str(index) + '. ' + k[0].decode('utf-8'))
                city_codes[str(index) + '. ' + k[0].decode('utf-8')] = v
                index += 1
        if not city_option:
            print u'cant find the city 哦'
            raise QueryError
        print ' '.join(city_option)
        while True:
            index = raw_input(u'input the city index u want.(eg:1)>>>')
            if index.isdigit() and int(index) <= len(city_option):
                from_city = city_option[int(index) - 1]
                from_code = city_codes[from_city][0]
                city_option = []
                city_codes = {}
                index = 1
                break
        to_city = raw_input('input the to city(eg:sh or 上海): '.decode('utf-8'))
        for k, v in sta_dict.items():
            if to_city in k:
                city_option.append(str(index) + '.' + k[0].decode('utf-8'))
                city_codes[str(index) + '.' + k[0].decode('utf-8')] = v
                index += 1
        if not city_option:
            print u'cant find the city 哦'
            raise QueryError
        print ' '.join(city_option)
        while True:
            index = raw_input(u'input the city index u want.(eg:1)>>>')
            if index.isdigit() and int(index) <= len(city_option):
                to_city = city_option[int(index) - 1]
                to_code = city_codes[to_city][0]
                break
        while True:
            m_d = {
                ('1', '3', '5', '7', '8', '10', '12'): '31',
                ('2',): '28',
                ('4', '6', '9', '11'): '30'
            }
            now = time.localtime()
            now = str(now[1]) + '-' + str(now[2])
            date = raw_input('input the date(eg:%s)' % now)
            m, d = re.split('[\.\-]', date)
            if 0 < int(m) < 13:
                for k, v in m_d.items():
                    if m in k:
                        if int(m) < 10: m = '0' + m
                        d_max = v
                if 0 < int(d) <= d_max:
                    date = '2017-' + m + '-' + d
                    break
            print 'mdzz'
        # # 如果之前已经查过该路线
        # if (from_city, to_city, date) in self.all_query:
        #     self.now_query = self.all_query[(from_city, to_city, date)]
        #     show(self.now_query)
        #     return
        left_tic_url = self.left_tic_url % (date, from_code, to_code)
        # print 'left_tic:'+left_tic_url
        cont = req_get(left_tic_url, self.query_headers)
        # print 'query left tic res:'+cont
        cont = json.loads(cont)
        tickets = cont['data']['result']
        train = []
        for ticket in tickets:
            cm = ticket.split('|')
            start_time = cm[8]
            arrive_time = cm[9]
            lishi= cm[10]
            canWebBuy = cm[11]
            station_train_code = cm[3]
            # get price arg
            train_no = cm[2]
            start_train_date = cm[13]
            start_train_date = date
            from_no = cm[16]
            to_no = cm[17]
            seat_types = cm[35]
            price_arg = station_train_code+'|'+train_no+'|'+from_no+'|'+to_no+'|'+seat_types+'|'+start_train_date
            self.now_price_arg.append(price_arg)
            # get order arg
            order_arg = []
            order_arg.append(cm[0])  # secretStr
            order_arg.append(from_city)
            order_arg.append(to_city)
            order_arg.append(date)
            order_arg.append(cm[15])  # train_localtion
            order_arg.append(canWebBuy)
            temp = u'车次:'+station_train_code+u'|出发:'+start_time+u',到达:'+arrive_time+u'|历时：'+lishi+'|'
            site = {}
            if cm[20]: site['gg_num'] = cm[20]
            if cm[21]: site[u'高级软卧'] = cm[21]
            if cm[22]: site['qt_num'] = cm[22]
            if cm[23]: site[u'软卧'] = cm[23]
            if cm[24]: site[u'软座'] = cm[24]
            if cm[25]: site[u'特等座'] = cm[25]
            if cm[26]: site[u'无座'] = cm[26]
            if cm[27]: site['yb_num'] = cm[27]
            if cm[28]: site[u'硬卧'] = cm[28]
            if cm[29]: site[u'硬座'] = cm[29]
            if cm[30]: site[u'二等座'] = cm[30]
            if cm[31]: site[u'一等座'] = cm[31]
            if cm[32]: site[u'商务座'] = cm[32]
            if cm[33]: site[u'动卧'] = cm[33]
            order_arg.append(site.keys())

            self.now_order_arg.append(order_arg)
            for k, v in site.items():
                temp = temp+k+':'+v+','
            temp = temp.strip(',')
            temp = temp+u'|可购:'+canWebBuy
            train.append(temp)
        self.now_query[(from_city, to_city, date)] = train
        self.all_price_arg.extend(self.now_price_arg)
        self.all_order_arg.extend(self.now_order_arg)
        self.all_query.update(self.now_query)
        show(self.now_query)

    def price(self, arg):
        price_args = []
        for price_arg in self.now_price_arg:
            price_args.append(price_arg.split('|'))
        while True:
            if not arg:
                index = raw_input("input the index(eg:1) for the ticket:")
            else:
                index = arg
            if not index or not index.isdigit() or int(index) <= 0 or int(index) > len(price_args):
                arg = ''
                continue
            args_list = price_args[int(index)-1][1:]  # train_no, from_no, to_no, seat_types, train_date
            price_url = self.price_url % tuple(args_list)
            # print 'price_url:'+price_url
            cont = json.loads(req_get(price_url, self.query_headers))
            # print 'price_cont:'+cont
            data = cont['data']
            price_info = price_args[int(index)-1][0]+'   '
            for k, v in data.items():
                v = str(v).replace(u'\xa5', '')
                if k == 'WZ': price_info += u'无座' + ':' + v + u'元,'
                if k == 'A1': price_info += u'硬座' + ':' + v + u'元,'
                if k == 'A2': price_info += u'软座' + ':' + v + u'元,'
                if k == 'A3': price_info += u'硬卧' + ':' + v + u'元,'
                if k == 'A4': price_info += u'软卧' + ':' + v + u'元,'
                if k == 'A6': price_info += u'高级软卧' + ':' + v + u'元,'
                if k == 'A9': price_info += u'商务座' + ':' + v + u'元,'
                if k == 'M': price_info += u'一等座' + ':' + v + u'元,'
                if k == 'O': price_info += u'二等座' + ':' + v + u'元,'
                if k == 'F': price_info += u'动卧' + ':' + v + u'元,'
            price_info = price_info.strip(',')
            print price_info
            break

    def before(self):
        show(self.all_query)
        self.now_price_arg = self.all_price_arg

    def order(self, arg):
        while True:
            qiang = False
            index = arg if arg else raw_input('input the ticket index u want order:')
            if not index or not index.isdigit() or int(index) <= 0 or int(index) > len(self.now_order_arg):
                arg = ''
                continue
            order_org = self.now_order_arg[int(index)-1]
            if order_org[-2] == 'N':
                print u'该火车票已售完,请使用抢票功能或选择其他票购买.'
                while True:
                    flag = raw_input(u'是否抢票(y/n):')
                    if flag!='y' or flag!='n': continue
                    if flag == 'y':
                        self.get_cookie()
                        show_seat = True
                        while True:
                            cont = req_get(self.left_tic_url, self.headers, self.session)
                            if cont and json.loads(cont).get('data', {}).get('result', []):
                                ticket_info = json.loads(cont)['data']['result'][int(index)-1]
                                cm = ticket_info.split('|')
                                site = {}
                                if cm[20]: site['gg_num'] = cm[20]
                                if cm[21]: site[u'高级软卧'] = cm[21]
                                if cm[22]: site['qt_num'] = cm[22]
                                if cm[23]: site[u'软卧'] = cm[23]
                                if cm[24]: site[u'软座'] = cm[24]
                                if cm[25]: site[u'特等座'] = cm[25]
                                if cm[26]: site[u'无座'] = cm[26]
                                if cm[27]: site['yb_num'] = cm[27]
                                if cm[28]: site[u'硬卧'] = cm[28]
                                if cm[29]: site[u'硬座'] = cm[29]
                                if cm[30]: site[u'二等座'] = cm[30]
                                if cm[31]: site[u'一等座'] = cm[31]
                                if cm[32]: site[u'商务座'] = cm[32]
                                if cm[33]: site[u'动卧'] = cm[33]
                                msg = ''
                                if show_seat:
                                    for index, seat in site.keys():
                                        msg += str(index+1)+'.'+seat+' '
                                    print msg
                                    index = raw_input(u'选择座位类型（0表示任意座位都行）')
                                break
                    break
                if not qiang: continue
            now = time.time()
            if now - self.login_time > 5 * 60:
                print u'登录信息过期.'
                self.get_cookie()
            if not self.check_user() or not self._submit_order(index):
                print u'提交订单失败，请重试或选择其他列车.'
                continue
            url = 'https://kyfw.12306.cn/otn/confirmPassenger/initDc'
            cont = req_post(url, self.headers, {'_json_att': ''}, self.session)
            # var globalRepeatSubmitToken = '562eedc566f431ae5be1e202b4c74523';
            token = re.search("globalRepeatSubmitToken = '(.+?)';", cont, re.S).group(1)
            key_check_isChange = re.search("'key_check_isChange':'(.+?)',", cont, re.S).group(1)
            leftTicketStr = re.search("'leftTicketStr':'(.+?)',", cont, re.S).group(1)
            self.get_users(token)
            print u'该账号下共有%d名用户：' % len(self.users)
            msg = ''
            index = 1
            for info in self.users:
                msg += str(index)+'.'+info['passenger_name']+' '
                index += 1
            print msg
            while True:
                index = raw_input(u'选择一位乘客：')
                if not index or not index.isdigit() or int(index) <= 0 or int(index) > len(self.users):
                    print u'what the shit you input'
                    continue
                user_raw = self.users[int(index)-1]
                user = {
                    'name': user_raw['passenger_name'],
                    'no': user_raw['passenger_id_no'],
                    'passenger_id_type_code': user_raw['passenger_id_type_code'],
                    'passenger_type': user_raw['passenger_type'],
                    'mobile_no': user_raw['mobile_no'] if user_raw['mobile_no'] else '',
                    'passenger_flag': user_raw['passenger_flag']
                }
                break
            index = 1
            msg = ''
            for seat in order_org[-1]:
                msg += str(index) + '.' + seat+' '
                index += 1
            print u'可选车票类型: ' + msg
            while 1:
                index = raw_input(u'选择座位类型：')
                if not index or not index.isdigit() or int(index) <= 0 or int(index) > len(order_org[-1]):
                    print u'what the shit you input'
                    continue
                seat = order_org[-1][int(index)-1]
                code = self.site_code[seat]
                break
            while 1:
                try:
                    check_order_info_url = 'https://kyfw.12306.cn/otn/confirmPassenger/checkOrderInfo'
                    print 'user'+user['name']
                    oldPassengerStr = user['name'] + ',1,' + user['no'] + ',1_'
                    passengerTicketStr = code+',0,1,'+user['name']+',1,'+user['no']+','+user['mobile_no']+',N'
                    data = {
                        'REPEAT_SUBMIT_TOKEN': token,
                        '_json_att': '',
                        'bed_level_order_num': '000000000000000000000000000000',
                        'cancel_flag': '2',
                        'oldPassengerStr': oldPassengerStr,
                        'passengerTicketStr': passengerTicketStr,
                        'randCode': '',
                        'tour_flag': 'dc'
                    }
                    print data
                    cont = req_post(check_order_info_url, self.headers, data, self.session)
                    print cont
                    confirm_order_url = 'https://kyfw.12306.cn/otn/confirmPassenger/confirmSingleForQueue'
                    data = {
                        'REPEAT_SUBMIT_TOKEN': token,
                        '_json_att': '',
                        'choose_seats': '',
                        'dwAll': 'N',
                        'key_check_isChange': key_check_isChange,
                        'leftTicketStr': leftTicketStr,
                        'oldPassengerStr': oldPassengerStr,
                        'passengerTicketStr': passengerTicketStr,
                        'purpose_codes': '00',
                        'roomType': '00',
                        'seatDetailType': '000',
                        'randCode': '',
                        'train_location': order_org[4]
                    }
                    print data
                    cont = req_post(confirm_order_url, self.headers, data, self.session)
                    print cont
                    print u'购票成功'
                    break
                except Exception as e:
                    print e















