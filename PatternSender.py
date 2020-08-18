import os
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class EmptyFileException(Exception):
    def __init__(self, error_messsage):
        self.text = error_messsage
        
class PatternSender:
    
    LOGIN = "tavrilam"
    PASSWORD = "gqKRkymu"
    AUTH_URL = "https://www.mql5.com/ru/auth_login"
    PROFILE_URL = "https://www.mql5.com/ru/users/"
    MAIL_URL = "https://www.mql5.com/ru/users/tavrilam/messages?user="
    MEMBERS = 9
    TIME_MIN_WAIT_MESSAGE = 3000
    TIME_MAX_WAIT_MESSAGE = 6000
    TIME_MIN_WAIT_CIRCLE = 4000
    TIME_MAX_WAIT_CIRCLE = 6000
    FLAG_MAIL_CHECK = 1
    MIN_RATING = 0
    MAX_RATING = 3000

    
    def __init__(self):
        self.start()
        
    def launch(self, browser_name='Firefox'):
        if browser_name == 'Firefox':
            self.driver = webdriver.Firefox(executable_path='.\geckodriver\geckodriver.exe')
            time.sleep(3)
        else:
            raise AttributeError('В данной версии, поддерживает только Firefox')
            
    def start(self):
        self.launch()
        self.auth()
        while True:
            for i in range(20):
                self.profile_name = self.get_record(path="profile.txt")               
                if self.check_profile(self.profile_name):
                    if self.FLAG_MAIL_CHECK:
                        if self.check_mail(self.profile_name):
                            rating = self.get_users_rating(self.profile_name)
                            print(rating, self.profile_name)
                            if rating >= self.MIN_RATING and rating<=self.MAX_RATING:
                                pattern = self.get_pattern()
                                self.send_mail(pattern)
                                self.log('Сообщение отправленно пользователю {}'.format(self.profile_name))
                                self.mark_user(self.profile_name, text="OK")
                            else:
                                self.log(f"Rating is not in range rating: {rating} - user: {self.profile_name}")
                    else:
                        pattern = self.get_pattern()
                        self.send_mail(pattern)
                        self.log('Сообщение отправленно пользователю {}'.format(self.profile_name))
                        self.mark_user(self.profile_name, text="OK")
            sleeping_time = random.randint(self.TIME_MIN_WAIT_CIRCLE, self.TIME_MAX_WAIT_CIRCLE) / 1000
            self.log("Цикл из {} пользователей завершен, засыпаю на {} секунд".format(self.MEMBERS, sleeping_time))
            time.sleep(sleeping_time)
            self.log("\n\n Возобновляю работу")
                
    def auth(self, login=LOGIN, password=PASSWORD):
        self.driver.get(self.AUTH_URL)
        time.sleep(3)
        self.driver.find_element_by_id('Login').send_keys(login)
        pass_field = self.driver.find_element_by_id('Password')
        pass_field.send_keys(password, Keys.ENTER)
        time.sleep(3)
        
    def log(self, text):
        with open('log.txt', 'a', encoding="utf-8") as f:
            time = datetime.strftime(datetime.now(), "[%Y-%m-%d %H:%M:%S] ")
            f.write(time + text + '\n')
            print(time + text)
            
    def get_record(self, path):
        with open(path) as f:
            buffer = f.read()
            buffer = buffer.split('\n')
            try:
                buffer.remove('')
            except:
                pass
            try:
                record = buffer.pop(0)
            except:
                self.log('Закончились записи в {}'.format(path))
                self.log('Завершаю работу \n')
                self.driver.close()
                raise EmptyFileException('Закончились записи в {}'.format(path))
                
        with open(path, 'w') as f:
            for line in buffer:
                f.write(line + '\n')
        if record[:6] == 'https:':
            return record
        return 'https://www.mql5.com/ru/users/'+record
    
    def get_pattern(self):
        def get_random_pattern(path):
            text = ''
            with open(path) as f:
                buffer = f.read()
                buffer = buffer.split('\n')     
                while text =='':
                    text = random.choice(buffer)
            return text
        pattern = get_random_pattern('hi-pattern.txt') + '$' + get_random_pattern('text-pattern.txt') + '$' + get_random_pattern('bye-pattern.txt')
        return pattern
                
    def mark_user(self, profile_name, text):
        with open('done.txt', 'a') as f:
            f.write(profile_name + ' - ' + text + '\n')
            
    def check_profile(self, profile_name):
        self.driver.get(profile_name)
        response = requests.get(profile_name)
        if response.status_code != 200:
            self.log(f"Страница {profile_name} не существует")
            return False
        time.sleep(3)
        bs_obj = BeautifulSoup(self.driver.page_source, 'html.parser')
        info_fields = bs_obj.findAll('div', class_='counterName')
        if len(info_fields) > 0:
            for field in info_fields:
                text = field.get_text().strip()
                if 'продукт' in text:
                    self.log("{} - продукты".format(profile_name))
                    self.mark_user(profile_name, text="have product")
                    return False
                if 'работ' in text:
                    self.log("{} - работы".format(profile_name))
                    self.mark_user(profile_name,text="have job")
                    return False
        return True
    
    def check_mail(self, profile_name):
        name = profile_name[len(self.PROFILE_URL):]
        self.driver.get(self.MAIL_URL + name)
        time.sleep(random.randint(self.TIME_MIN_WAIT_MESSAGE, self.TIME_MAX_WAIT_MESSAGE) / 1000)
        bs_obj = BeautifulSoup(self.driver.page_source, 'html.parser')
        messages = bs_obj.findAll('div', class_="chatWidgetCommentText")
        if len(messages):
            self.log("{} - уже общались".format(profile_name))
            self.mark_user(profile_name,text="have message")
            return False
        return True
    
    def get_users_rating(self,name):
        try:
            page = BeautifulSoup(requests.get(name).text, 'lxml')
            tables = page.find("table", {"id" : "mainDetails"})
            try:
                return int(list(tables.findAll("a"))[-1].text)
            except:
                try:
                    return int(list(tables.findAll("a"))[-2].text)
                except:
                    return self.MIN_RATING
        except Exception as e:
            print(e)
            return self.MIN_RATING

    def send_mail(self, pattern):
        bs_obj = BeautifulSoup(self.driver.page_source, 'html.parser')
        name = bs_obj.find(class_="chatWidgetCommentsListUserLink").get_text()
        message = pattern.replace("#login", name)
        messages = message.split('$')
        self.profile_name = self.get_record(path="profile.txt")
        try:
            for message in messages:
                self.driver.find_element_by_tag_name('textarea').send_keys(message)
                self.driver.find_element_by_tag_name('textarea').send_keys(Keys.ENTER)
            self.driver.find_element_by_css_selector('button[type="button"]').click()
        except:
            self.log("Can't find send button")

        time.sleep(2)   
        
if __name__ == "__main__":
    a = PatternSender()
        
