# coding=utf-8

import redis
import requests
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
import pdb
import time
import hashlib
from random import choice
from random import Random
import os
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
            dr = webdriver.PhantomJS(desired_capabilities=dcap)
            dr.get(url)
            dr.implicitly_wait(30)
            if dr.find_element_by_id('username'):
                name = dr.find_element_by_id('username')
                pw = dr.find_element_by_id('password')
                name.clear()
                pw.clear()
                name.send_keys(user.split('|')[0])
                pw.send_keys(user.split('|')[1])
                dr.find_element_by_id('btnLogin').click()
                #  dr.implicitly_wait(60)
                #  time.sleep(15)
                time.sleep(10)
                sleep_time = 0
                retry_time = 0
                while ('mycenter' not in dr.current_url) and (retry_time < 10):
                    sleep_time += 0.5
                    retry_time += 1
                    time.sleep(sleep_time)
                print dr.current_url
                soup = bs(dr.page_source, 'lxml')
                cks = dr.get_cookies()
                dr.quit()
                u = soup.find_all('h3')[0].text
                if u == user.split('|')[0]:
                    print("Get Cookie Success!( Account:%s )" % user)
                    cookies = {}
                    for x in cks:
                        cookies[x['name']] = x['value']
                    return json.dumps(cookies)
        except:
            dr.quit()
            pdb.set_trace()
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
