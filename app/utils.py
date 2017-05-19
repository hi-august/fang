# coding=utf-8

import redis
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import ipdb
import time
import hashlib
from random import choice
from random import Random
import os
import signal
import sys
sys.path.append(os.getcwd())
#  print sys.path
import config as settings

#  import os
#  import sys
#  path = os.path.abspath(os.getcwd())
#  print(path)
#  sys.path.append(path)
users = [
    'zyf23456789|cxk517',
]


dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = (
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36'
)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36',
}

def md5(msg):
    md5 = hashlib.md5(msg.encode('utf-8')).hexdigest()
    return md5

def random_str(randomlength=6):
    str = ''
    chars = 'AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

def ecp(im, dcount=6):
    frame = im.load()
    (w, h) = im.size
    for i in xrange(w):
        for j in xrange(h):
            if frame[i, j] != 255:
                count = 0
                try:
                    if frame[i, j - 1] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i, j + 1] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i - 1, j - 1] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i - 1, j] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i - 1, j + 1] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i + 1, j - 1] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i + 1, j] == 255:
                        count += 1
                except IndexError:
                    pass
                try:
                    if frame[i + 1, j + 1] == 255:
                        count += 1
                except IndexError:
                    pass
                if count >= dcount:
                    frame[i, j] = 255
    return im

_redis_pool_list = {}
def get_redis(name):
    if name not in _redis_pool_list:
        if not settings.REDIS_PASS:
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                socket_timeout=10,
                db=0,
            )
        else:
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASS,
                socket_timeout=10,
                db=0,
            )

        _redis_pool_list[name] = pool
    return redis.Redis(connection_pool=_redis_pool_list[name])

class RobotConsumer(object):
    name = 'base'

    def __init__(self):
        self.dr = webdriver.PhantomJS(desired_capabilities=dcap)
        #  self.dr = webdriver.Firefox()

    def close(self):
        # 这里需手动关闭
        # f = AjkRobot()
        # cks = f.get_good_robot()
        # f.close()
        # 防止phantomjs没有完全退出
        self.dr.service.process.send_signal(signal.SIGTERM)
        self.dr.quit()

    def valid_robot(self, cookies):
        return True

    def get_robot(self):
        rds = get_redis("default")
        cookies = rds.srandmember(self.name)
        return cookies

    def on_producer_add(self, cookies):
        if self.valid_robot(cookies):
            self.add_robot(cookies)

    def on_producer_remove(self, cookies):
        self.remove_robot(cookies)

    def add_robot(self, cookies):
        rds = get_redis("default")
        add_cnt = rds.sadd(self.name, cookies)
        return add_cnt


    def remove_robot(self, cookies):
        rds = get_redis("default")
        del_cnt = rds.srem(self.name, cookies)
        return del_cnt

    def all_robot(self):
        rds = get_redis("default")
        return rds.smembers(self.name)

    def robot_size(self):
        rds = get_redis("default")
        return rds.scard(self.name)

class FangRobot(RobotConsumer):
    name = 'fang:cookies'

    def valid_robot(self, cookies):
        try:
            url = 'https://m.fang.com/my/?c=mycenter'
            res = requests.get(url,
                               #  headers=headers,
                               cookies=json.loads(cookies),
                               #  proxies=proxies,
                               )
            uu = bs(res.content, 'lxml').find_all('h3')[0].text
            if uu:
                print('Cookies Success valid_robot ==> %s'%uu)
                return True
            else:
                print('Cookies is Failed!!!')
                return False
        except Exception as e:
            print(e)
            print('Cookies is Failed!!!')
            return False

    def get_good_robot(cls, retry=0):
        cookies = cls.get_robot()
        if not cookies:
            cls.add_random_robot(1)
        if cls.valid_robot(cookies):
            try:
                return json.loads(cookies)
            except Exception as e:
                print(e, cookies)
                return cookies
        else:
            cls.remove_robot(cookies)
            retry += 1
            if retry > 2:
                return None
            return cls.get_good_robot(retry=retry)

    def add_cookies(self, user):
        url = 'https://m.fang.com/passport/login.aspx'
        try:
            self.dr.get(url)
            self.dr.implicitly_wait(30)
            if self.dr.find_element_by_id('username'):
                name = self.dr.find_element_by_id('username')
                pw = self.dr.find_element_by_id('password')
                name.clear()
                pw.clear()
                name.send_keys(user.split('|')[0])
                pw.send_keys(user.split('|')[1])
                self.dr.find_element_by_id('btnLogin').click()
                #  dr.implicitly_wait(60)
                #  time.sleep(15)
                time.sleep(10)
                sleep_time = 0
                retry_time = 0
                while ('mycenter' not in self.dr.current_url) and (retry_time < 10):
                    sleep_time += 0.5
                    retry_time += 1
                    time.sleep(sleep_time)
                print self.dr.current_url
                soup = bs(self.dr.page_source, 'lxml')
                cks = self.dr.get_cookies()
                u = soup.find_all('h3')[0].text
                if u == user.split('|')[0]:
                    print("Get Cookie Success!( Account:%s )" % user)
                    cookies = {}
                    for x in cks:
                        cookies[x['name']] = x['value']
                    return json.dumps(cookies)
        except:
            ipdb.set_trace()
            return ''


    def add_random_robot(cls, default=30):
        try:
            redis_faxin_users = [json.loads(y)['username'] for y in cls.all_robot()]
        except:
            redis_faxin_users = []
        for x in xrange(default):
            user = choice(users)
            if user not in redis_faxin_users:
                print('add_random_robot %s' %(user))
                cookies = cls.add_cookies(user)
                cls.add_robot(cookies)
                if cookies and default==1:
                    return cookies

class AjkRobot(RobotConsumer):
    name = 'ajk:cookies'


    def valid_robot(self, cookies):
        try:
            url = 'http://user.anjuke.com/user/message'
            #  dr = webdriver.Firefox()
            self.dr.set_page_load_timeout(10)
            self.dr.set_script_timeout(10)
            self.dr.get(url)
            try:
                for x in json.loads(cookies):
                    self.dr.add_cookie(x)
            except:
                pass
            self.dr.get(url)
            #  ipdb.set_trace()
            try:
                uu = bs(self.dr.page_source, 'lxml').find('li', attrs={'class': 'user-account'}).text.strip()
            except:
                uu = ''
            if uu:
                print('Cookies Success valid_robot ==> %s'%uu)
                return True
            else:
                print('Cookies is Failed!!!')
                return False
        except Exception as e:
            print(e)
            print('Cookies is Failed!!!')
            return False

    def get_good_robot(cls, retry=0):
        cookies = cls.get_robot()
        if not cookies:
            cls.add_random_robot(1)
        if cls.valid_robot(cookies) and cookies:
            try:
                return json.loads(cookies)
            except Exception as e:
                print(e, cookies)
                return cookies
            finally:
                pass
                #  ipdb.set_trace()
        else:
            cls.remove_robot(cookies)
            retry += 1
            if retry > 2:
                return None
            return cls.get_good_robot(retry=retry)

    def add_cookies(self, user):
        #  url = 'http://login.anjuke.com/login/iframeform'
        url = 'http://login.anjuke.com/login/form?history=aHR0cDovL3NoZW56aGVuLmFuanVrZS5jb20v'
        try:
            #  dr = webdriver.Firefox()
            #  dr = webdriver.PhantomJS(desired_capabilities=dcap)
            self.dr.get(url)
            #  ipdb.set_trace()
            self.dr.implicitly_wait(30)
            # 切换ifame
            self.dr.switch_to_frame(self.dr.find_element_by_id("iframeLoginIfm"))
            if self.dr.find_element_by_id('pwdTab'):
                self.dr.find_element_by_id('pwdTab').click()
            #  ipdb.set_trace()
            if self.dr.find_element_by_id('pwdUserNameIpt'):
                name = self.dr.find_element_by_id('pwdUserNameIpt')
                pw = self.dr.find_element_by_id('pwdIpt')
                name.clear()
                pw.clear()
                name.send_keys(user.split('|')[0])
                pw.send_keys(user.split('|')[1])
                self.dr.find_element_by_id('pwdSubmitBtn').click()
                self.dr.implicitly_wait(60)
                sleep_time = 0
                retry_time = 0
                while ('loginSuccess : "1"' not in self.dr.page_source) and (retry_time < 10):
                    sleep_time += 0.5
                    retry_time += 1
                    time.sleep(sleep_time)
                if 'loginSuccess : "1"' in self.dr.page_source:
                    cks = self.dr.get_cookies()
                    print self.dr.current_url
                    print("Get Cookie Success!( Account:%s )" % user)
                    cookies = {}
                    tmp = ''
                    for x in cks:
                        cookies[x['name']] = x['value']
                        tmp += x['name'] + '=' + x['value'] + ';'
                    headers['Cookie'] = tmp
                    headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    #  print bs(dr.page_source, 'lxml').find('li', attrs={'class': 'user-account'}).text.strip()
                    #  ipdb.set_trace()
                    return json.dumps(cks)
        except:
            return ''

    def add_random_robot(cls, default=30):
        #  try:
            #  redis_faxin_users = [json.loads(y)['username'] for y in cls.all_robot()]
        #  except:
            #  redis_faxin_users = []
        users = ['15338702029|cxk517']
        redis_faxin_users = []
        for x in xrange(default):
            user = choice(users)
            if user not in redis_faxin_users:
                print('add_random_robot %s' %(user))
                cookies = cls.add_cookies(user)
                cls.add_robot(cookies)
                if cookies and default==1:
                    return cookies
