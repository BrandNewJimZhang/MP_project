import os
import sys
import requests as rs
import re
from bs4 import BeautifulSoup as bs
import time
from faker import Faker
from threading import Thread, Lock
import queue


class UrlResponError(OSError):
    pass


class LogFileNotFoundError(FileNotFoundError):
    pass


class CONFIG:
    '''
    '''
    ROOT_DOMAIN = r'https://www.51voa.com'
    MASTR_URL = r'https://www.51voa.com/VOA_Standard_{}.html'
    HEAD = {
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
    }
    URL_QUEUE = queue.Queue()
    MP3_QUEUE = queue.Queue()
    MESSAGE_QUEUE = queue.Queue()
    START_TIME = time.time()
    SPIDER_NUM = 5
    COMPLETE_LIST = [i for i in range(0, 36)]
    COMPLETE_MP3 = [[0 for __ in range(50)]] + [[1 for __ in range(50)]
                                                for _ in range(0, 35)]
    LOCK = Lock()

    @staticmethod
    def refresh_status():
        '''
        '''
        with CONFIG.LOCK:
            for i in range(len(CONFIG.COMPLETE_MP3)):
                if sum(CONFIG.COMPLETE_MP3[i]) == 0:
                    CONFIG.COMPLETE_LIST[i] = 0
        pass

    @staticmethod
    def get_html(url):
        '''
        '''
        for i in range(11):
            try:
                r = rs.get(url, headers=CONFIG.HEAD)
                if r.status_code == 200:
                    return r
            except rs.exceptions.ProxyError:
                if i == 10:
                    raise UrlResponError(
                        'Unable to get an effective response from {}!'.format(
                            url))
                else:
                    continue

    @staticmethod
    def send_message(message):
        '''
        '''
        CONFIG.MESSAGE_QUEUE.put(message)
        pass

    @staticmethod
    def receive_message():
        '''
        '''
        return CONFIG.MESSAGE_QUEUE.get()


class MainPageSpider(Thread):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.curnum = None
        pass

    def get_url_list(self):
        '''
        '''
        r = CONFIG.get_html(CONFIG.MASTR_URL.format(self.curnum))
        r.encoding = 'utf-8'
        soup = bs(r, 'lxml')
        sub_url = soup.find('div', class_='List')
        urls = sub_url.find_all('li')
        urls_dict = {}
        for i in urls:
            urls_dict[' '.join(
                i.text.split())] = CONFIG.ROOT_DOMAIN + i.a.get('href')
        return urls_dict

    def send_urls_dict(self, urls_dict: dict):
        '''
        '''
        res = {'No': self.curnum, 'urls': urls_dict}
        CONFIG.URL_QUEUE.put(res)
        pass

    def send_none(self):
        '''
        '''
        for _ in range(CONFIG.SPIDER_NUM):
            CONFIG.URL_QUEUE.put(None)

    def creat_folder(self):
        '''
        '''
        for i in ['mp3', 'lrc', 'article', 'translate', 'markdowm']:
            dirpath = './week 13/51voa/{}/{}'.format(self.curnum, i)
            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            else:
                continue
        pass

    def run(self):
        for i in CONFIG.COMPLETE_LIST:
            if i != 0:
                self.curnum = id
            else:
                continue
            res = self.get_url_list()
            self.send_urls_dict(res)
            self.creat_folder()
        self.send_none()
        pass


class ArticleSpider(Thread):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.r = None
        self.curnum = None
        self.curmp3num = 0
        self.curdict = None
        self.curtitle = None
        self.cururl = None
        pass

    def get_urls_dict(self):
        '''
        '''
        urls_dict = CONFIG.URL_QUEUE.get()
        if urls_dict is None:
            return None
        else:
            self.curnum = urls_dict['No']
            self.curnum = urls_dict['urls']
            return 1

    def get_url(self):
        '''
        '''
        self.r = CONFIG.get_html(self.cururl)
        pass

    def get_article(self, save_to):
        '''
        '''
        r = self.r
        r.encoding = 'utf-8'
        soup = bs(r, 'lxml')
        article = soup.find('div', class_='Content')
        res = []
        for i in article.find_all('p'):
            res.append(' '.join(i.text.split()))
        with open(save_to, 'w', encoding='utf-8') as f:
            for i in res:
                f.write(i)
                f.write('\n')
            f.flush()
        pass

    def get_mp3_info(self):
        '''
        '''
        r = self.r
        r.encoding = 'utf-8'
        soup = bs(r, 'lxml')
        mp3_url = soup.find('div', class_='menubar')
        mp3_info_dict = {
            'No':
            self.curnum,
            'subNo':
            self.curmp3num,
            'title':
            self.curtitle,
            'mp3':
            mp3_url.find('a', id='mp3').get('href'),
            'lrc':
            CONFIG.ROOT_DOMAIN + mp3_url.find('a', id='lrc').get('href'),
            'translate':
            CONFIG.ROOT_DOMAIN + r'/VOA_Standard_English/' +
            mp3_url.find('a', id='EnPage').get('href')
        }
        return mp3_info_dict

    def get_translate(url, save_to):
        '''
        '''
        r = CONFIG.get_html(url)
        r.encoding = 'utf-8'
        soup = bs(r, 'lxml')
        article = soup.find('div', class_='Content')
        res = []
        for i in article.find_all('p'):
            res.append(' '.join(i.text.split()))
        with open(save_to, 'w', encoding='utf-8') as f:
            for i in res:
                f.write(i)
                f.write('\n')
            f.flush()
        pass

    def send_mp3_info(self, mp3_info_dict):
        '''
        '''
        CONFIG.MP3_QUEUE.put(mp3_info_dict)
        pass

    def send_none():
        '''
        '''
        for _ in range(CONFIG.SPIDER_NUM):
            CONFIG.MP3_QUEUE.put(None)

    def run(self):
        while True:
            urls_dict = self.get_urls_dict()
            if urls_dict is None:
                break
            else:
                for self.curtitle, self.cururl in self.curdict.items():
                    self.curmp3num += 1
                    self.get_url()
                    self.get_article(
                        r'./week 13/51voa/{}/article/{}.txt'.format(
                            self.curnum, self.curtitle))
                    mp3_info = self.get_mp3_info()
                    self.get_translate(
                        mp3_info['translate'],
                        r'./week 13/51voa/{}/translate/{}.txt'.format(
                            self.curnum, self.curtitle))
                    self.send_mp3_info(mp3_info)
        self.send_none()
        pass


class MP3Spider(Thread):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.curnum = None
        self.curmp3num = None
        self.curtitle = None
        self.curmp3url = None
        self.curlrcurl = None
        self.curmem = None
        self.nonecnt = 0
        pass

    def get_mp3_info(self):
        '''
        '''
        mp3_info = CONFIG.MP3_QUEUE.get()
        if mp3_info is None:
            self.nonecnt += 1
            if self.nonecnt == CONFIG.SPIDER_NUM:
                return None
            return 0
        else:
            self.curnum = mp3_info['No']
            self.curmp3num = mp3_info['subNo']
            self.curtitle = mp3_info['title']
            self.curmp3url = mp3_info['mp3']
            self.curlrcurl = mp3_info['lrc']
            return 1

    def get_music(self, save_to):
        '''
        '''
        r = CONFIG.get_html(self.curmp3url)
        r.encoding = 'utf-8'
        with open(save_to, 'w', encoding='utf-8') as f:
            f.write(r.content)
            f.flush()
        self.curmem = os.path.getsize(save_to)
        pass

    def get_lrc(self, save_to):
        '''
        '''
        r = CONFIG.get_html(self.curlrcurl)
        r.encoding = 'utf-8'
        with open(save_to, 'w', encoding='utf-8') as f:
            f.write(r.content)
            f.flush()
        pass

    def send_mem_info(self):
        '''
        '''
        CONFIG.send_message(self.curmem)
        pass

    def send_none(self):
        '''
        '''
        for _ in range(CONFIG.SPIDER_NUM):
            CONFIG.MESSAGE_QUEUE.put(None)

    def update_mp3_state(self):
        '''
        '''
        CONFIG.COMPLETE_MP3[self.curnum][self.curmp3num] = 0

    def run(self):
        while True:
            res = self.get_mp3_info()
            if res is None:
                break
            elif res == 0:
                continue
            else:
                self.get_music(r'./week 13/51voa/{}/mp3/{}.txt'.format(
                    self.curnum, self.curtitle))
                self.get_lrc(r'./week 13/51voa/{}/lrc/{}.txt'.format(
                    self.curnum, self.curtitle))
                self.send_mem_info()
                self.update_mp3_state()
        self.send_none()
        pass


class SpiderMonitor(Thread):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.num_of_files = 0
        self.cnt_num = 0
        self.cnt_mem = 0
        self.run_time = 0
        self.remain_time = 0
        self.remain_mem = 0
        self.nonecnt = 0
        pass

    def cnf(self):
        '''
        cnf stand for caculate number of files
        '''
        flag = 0
        for i in CONFIG.COMPLETE_LIST:
            if i != 0:
                flag += 1
        self.num_of_files = flag * 50
        pass

    def cot(self):
        '''
        cot stand for continuous operation time
        '''
        self.run_time = time.time() - CONFIG.START_TIME
        pass

    def etc(self):
        '''
        etc stand for estimated time of completion
        '''
        temp = self.num_of_files * self.run_time / self.cnt_num
        self.remain_time = temp - self.run_time
        pass

    def emc(self):
        '''
        emc stand for estimated memory of completion
        '''
        temp = self.num_of_files * self.cnt_mem / self.cnt_num
        self.remain_mem = temp - self.cnt_mem
        pass

    def get_state(self):
        '''
        '''
        message = CONFIG.receive_message()
        if message is None:
            self.nonecnt += 1
            if self.nonecnt == CONFIG.SPIDER_NUM:
                return None
            return 0
        self.cnt_num += 1
        self.cnt_mem += message
        self.cot()
        self.etc()
        self.emc()
        return -1

    def run(self):
        self.cnf()
        while True:
            flag = self.get_state()
            if flag is None:
                print('Complete')
                break
            os.system('clear')
            stat = '''Run Time : {} s\nSpider Rate : {}/{}\nMemory Usaged : {} MB\nRemain Time : {} s, Remain Menory : {} MB\n, Numer of Running Spiders : {}'''.format(
                self.run_time, self.cnt_num, self.num_of_files,
                self.cnt_mem / (1024 * 1024), self.remain_time,
                self.remain_mem / (1024 * 1024),
                CONFIG.SPIDER_NUM - self.nonecnt)
            print(stat)
            time.sleep(1)


class SpiderRecovery(Thread):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.id = 0
        pass

    def backup(self, path=r'./week 13/.log'):
        '''
        '''
        CONFIG.refresh_status()
        backup_dict = {
            'id': self.id,
            'time': '{} s'.format(time.time() - CONFIG.START_TIME),
            'state': CONFIG.COMPLETE_LIST
        }
        self.id += 1
        with open(path, 'a+') as f:
            f.write(str(backup_dict))
            f.write('\n')
        pass

    @staticmethod
    def recovery(path=r'./week 13/.log'):
        '''
        '''
        if not os.path.exists(path):
            raise LogFileNotFoundError('No such log file {} !'.format(path))
        with open(path, 'r') as f:
            lines = f.read().strip().split('\n')
            data = lines[-1]
        if data == '':
            print('No data to recovery')
            return None
        else:
            data = eval(data)
            with CONFIG.LOCK:
                CONFIG.COMPLETE_LIST = data['state']
                for i in range(len(CONFIG.COMPLETE_LIST)):
                    if CONFIG.COMPLETE_LIST[i] == 0:
                        CONFIG.COMPLETE_MP3[i] = [0 for _ in range(50)]
            print('Successfully recovery to time : {}'.format(data['time']))
        pass

    def run(self):
        while True:
            if sum(CONFIG.COMPLETE_LIST) == 0:
                break
            else:
                self.backup()
                time.sleep(60)
        pass


class Master:
    '''
    '''
    def __init__(self):
        pass

    def creat_

    def run(self):
        pass


def main():
    t = Master()
    t.run()
    pass


if __name__ == '__main__':
    main()
    pass
