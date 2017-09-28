# -*- coding:utf-8 -*-
__author__ = '9527'
__date__ = '2017/9/18 13:55'

import re
import time
from cmd import Cmd
from ticket import Ticket, QueryError
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class Client(Cmd):
    def __init__(self):
        Cmd.__init__(self)
        self.prompt = '12306>'
        self.intro = '''
            Welcome to 12306 Cmd Client
                   Author : 9527
                  Time : %s
          Input help for more information
        ''' % time.strftime('%X', time.localtime())
        self.tic = Ticket()

    def do_help(self, arg):
        print u'''
            query : query tickets
            price : look the price of the ticket which you query just now
            order : query tickets and order you want
            before: show all query
            exit  : we say goodbye
           That's All ! Have a try!
        '''

    def do_query(self, arg):
        try:
            self.tic.query()
        except (QueryError, KeyError):
            print u'what the fuck u input!'
        except Exception, e:
            print e
            print u'no result'

    def do_price(self, arg):
        self.tic.price(arg)

    def do_before(self, arg):
        self.tic.before()

    def do_order(self, arg):
        self.tic.order(arg)

    def do_exit(self):
        print 'cry to say bye'
        sys.exit()

    do_EOF = do_exit

if __name__ == '__main__':
    client = Client()
    client.cmdloop()
