import os
import time
import random
import pymongo
from PIL import Image
from io import BytesIO
from cookiespool import util
from selenium import webdriver
from cookiespool.config import *
from selenium.webdriver import ActionChains
from login.chaojiying import Chaojiying_Client
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from login.proxy_extension import create_proxy_auth_extension

class CookiesGenerate(object):
    def __init__(self, username, password):
        self.url = 'https://xueqiu.com/'
        self.username = username
        self.password = password
        self.__init__chrome_option()

    def __init__chrome_option(self):
        self.option = webdriver.ChromeOptions()
        #chrome 配置
        self.option.add_argument("--window-size=1920x1080")
        self.option.add_argument("--start-maximized")
        self.option.add_argument('--headless')
        self.option.add_argument('user-agent=' + random.choice(USER_AGENTS))

        #代理配置
        if PROXY_ENABLED:
            proxy = random.choice(PROXY)
            proxy_auth_plugin_path = create_proxy_auth_extension(
                proxy_host=proxy['PROXYHOST'],
                proxy_port=proxy['PROXYPORT'],
                proxy_username=proxy['PROXYUSER'],
                proxy_password=proxy['PROXYPASS'])
            self.option.add_extension(proxy_auth_plugin_path)


    def open(self):
        self.browser = webdriver.Chrome(chrome_options=self.option)
        self.browser.delete_all_cookies()
        self.browser.get(self.url)
        self.wait = WebDriverWait(self.browser, 5)
        if PROXY_ENABLED:
            #若开启代理，会弹出一个奇怪的界面，点击首页
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/nav/div/div[1]/div/a[1]'))).click()
        #找到首页上的登录按钮并点击
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="app"]/nav/div[1]/div[2]/div/div'))).click()
        #找到登录界面的微博登录按钮并点击
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[1]/div/div/div[2]/div[5]/ul/li[3]/a/i'))).click()
        # 
        self.browser.switch_to.window(self.browser.window_handles[1])
        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="jump_login_url_a"]'))).click()
        #找到账号密码登录按钮并点击
        time.sleep(0.5)
        #self.browser.switch_to.window(self.browser.window_handles[1])
        input_u = self.browser.find_element_by_id('username')
        input_u.send_keys(self.username)
        input_p = self.browser.find_element_by_id('password')
        input_p.send_keys(self.password)

    ###################-----------OCR验证码------------------------#####################
    def ocr_main(self):
        # 获取验证码图片并下载到本地
        time.sleep(1)
        scimg = self.wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="check_img"]')))
        self.browser.save_screenshot(self.Imgpath)
        top = 305
        bottom = top + 35
        left = 415
        right = left + 100
        img = Image.open(self.Imgpath).crop((left,top,right,bottom))
        img = img.convert('L')
        img.save(self.Imgpath)

        # 用超极鹰识别出图片张的文字
        text = self.captcha_identify()
        
        if text:
            input_c = self.wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="door"]')))
            input_c.send_keys(text)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="vForm"]/div[2]/div/ul/li[7]/div[1]/input'))).click()
        else:
            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="check_img"]'))).click()
            self.ocr_main()
            
    #def input_captcha(self, captcha_text):
    #    input_c = self.browser.find_element_by_xpath('//*[@id="outer"]/div/div[2]/form/div/div[1]/div[1]/p[3]/input')
    #    input_c.send_keys(captcha_text)
    #    self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="outer"]/div/div[2]/form/div/div[2]/div/p/a[1]'))).click()

    def get_file_content(self, filePath):
        with open(filePath, 'rb') as fp:
            return fp.read()

    def captcha_identify(self):
        '''用超极鹰进行识别'''
        img  = open(self.Imgpath, 'rb').read()
        chaojiying = Chaojiying_Client('kingdatalab', 'zju211root', '96001')
        result = chaojiying.PostPic(img, 1902)
        if result['err_no'] == -1005:
            print('无可用题分，请给超极鹰充值')
        text = result['pic_str']
        return text

###################-----------滑块验证码------------------------#####################
    #获取原图
    def get_position(self, xpath):
            img = self.wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            location = img.location
            size = img.size
            top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size['width']
            return (top, bottom, left, right)

    def get_screenshot(self):
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def get_image(self):
        # 根据网页实际情况，这里手动定义位置，确保抓下来图片大小一样，此处为非headless模式下的位置
        #top = 129
        #bottom = top+160
        #left = 247
        #right =left +260
        
        # headless下的位置
        top = 182
        bottom = top+160
        left = 255
        right =left +260

        screenshot = self.get_screenshot()
        captcha = screenshot.crop((left, top, right, bottom))
        return captcha

    def get_distance(self, image1,image2):
        '''
        拿到滑动验证码需要移动的距离
        :param image1:没有缺口的图片对象
        :param image2:带缺口的图片对象
        :return:需要移动的距离
        '''
        threshold=100
        left=50
        for i in range(left,image1.size[0]):
            for j in range(image1.size[1]):
                rgb1=image1.load()[i,j]
                rgb2=image2.load()[i,j]
                res1=abs(rgb1[0]-rgb2[0])
                res2=abs(rgb1[1]-rgb2[1])
                res3=abs(rgb1[2]-rgb2[2])
                if not (res1 < threshold and res2 < threshold and res3 < threshold):
                    return i - 7
        return i - 7


    def get_tracks(self, distance):
        '''
        拿到移动轨迹，模仿人的滑动行为，先匀加速后匀减速
        匀变速运动基本公式：
        ①v=v0+at
        ②s=v0t+½at²
        ③v²-v0²=2as

        :param distance: 需要移动的距离
        :return: 存放每0.3秒移动的距离
        '''
        #初速度
        v=0
        #单位时间为0.2s来统计轨迹，轨迹即0.2内的位移
        t=0.3
        #位移/轨迹列表，列表内的一个元素代表0.2s的位移
        tracks=[]
        #当前的位移
        current=0
        #到达mid值开始减速
        mid=distance*4/5

        while current < distance:
            if current < mid:
                # 加速度越小，单位时间的位移越小,模拟的轨迹就越多越详细
                a= 7 #+ random.random()
            else:
                a=-9 #+ random.random()

            #初速度
            v0=v
            #0.2秒时间内的位移
            s=v0*t+0.5*a*(t**2)
            #当前的位置
            current+=s
            #添加到轨迹列表
            tracks.append(round(s))

            #速度已经达到v,该速度作为下次的初速度
            v=v0+a*t
        return tracks

    def move_to_gap(self, slider, tracks):
        # 实例化一个action对象
        time.sleep(0.5)
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in tracks:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=random.randint(-1,1)).perform()
        captcha = self.get_image()
        captcha.save('login/template/result.png')
        time.sleep(1)
        ActionChains(self.browser).release().perform()

    def verify_successfully(self):
        if len(self.browser.window_handles) == 2:
            return False
        else:
            print('GEETEST验证成功')
            return True

    def error_test(self):
        '''在点击刷新后可能会出现错误提示，要点击后才能继续刷新'''
        try:
            error_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_panel_error_content'))).click()
            time.sleep(1)
        except:
            print('Geetest no error')
        return

    def geetest_main(self):
        # 执行js操作，隐藏滑块，获取有缺口图片
        element = self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div[2]/div[6]/div/div[1]/div[1]/div/a/div[1]/div/canvas[2]')))
        self.browser.execute_script("arguments[0].setAttribute('style', 'display:none')", element)
        # 截图，截取有缺口图片
        time.sleep(2)
        captcha_cut = self.get_image()
        captcha_cut.save('login/template/cut.png')
        self.browser.execute_script("arguments[0].setAttribute('style', 'display:block')", element)

        #将缺口图片还原出原图
        element = self.wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div/div[2]/div[6]/div/div[1]/div[1]/div/a/div[1]/canvas')))
        self.browser.execute_script("arguments[0].setAttribute('style', 'display:block')", element)
        time.sleep(2)
        captcha_full = self.get_image()
        captcha_full.save('login/template/full.png')
        self.browser.execute_script("arguments[0].setAttribute('style', 'display:none')", element)
        
        

        #获取移动轨迹
        distance = self.get_distance(captcha_full, captcha_cut)
        tracks=self.get_tracks(distance)
         #滑动验证
        slider = self.wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/div[2]/div[6]/div/div[1]/div[2]/div[2]')))
        self.move_to_gap(slider, tracks)
    
    def alert_box(self):
        try:
            prompt = Alert(self.browser)
            time.sleep(1)
            prompt.accept()
        except:
            return
###################-----------获取cookies------------------------#####################
    def get_cookie(self):
        cookies = self.browser.get_cookies()
        cookie = {}
        for item in cookies:
            if item['name']=='xq_a_token':
                cookie[item['name']] = item['value']
        return cookie

    def main(self):
        count = 1
        try:
            while True:
                self.open()
                time.sleep(0.5)
                #OCR验证码识别
                self.Imgpath = 'login/template/screenImg.png'
                self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="vForm"]/div[2]/div/ul/li[7]/div[1]/input'))).click()
                print('开始进行OCR验证')
                ocr_count = 1
                while True:
                    self.ocr_main()
                    time.sleep(2)
                    if 'https://api.weibo.com/oauth2/authorize' in self.browser.current_url:
                        self.browser.switch_to.window(self.browser.window_handles[1])
                        try:
                            self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="email"]'))).click()
                        except:
                            print('已连接雪球')
                        # 点击允许授权
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="outer"]/div/div[2]/div/div[2]/div[2]/p/a[1]'))).click()
                        print('OCR验证成功')
                        break
                    elif count < 5:
                        # 点击换一换按钮，换验证码图片
                        self.wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="outer"]/div/div[2]/form/div/div[1]/div[1]/p[3]/a'))).click()
                        count = count + 1
                    else:
                        print('OCR验证失败')
                        self.browser.quit()
                        cookie = None
                        return cookie
                self.alert_box()
                ##########滑块验证码
                if len(self.browser.window_handles) == 2:
                    print('开始GEETEST验证')
                    self.geetest_main()
                    time.sleep(5)
                    success = self.verify_successfully()
                    if success:
                        self.browser.switch_to.window(self.browser.window_handles[0])
                        cookie = self.get_cookie()
                        self.browser.quit()
                        print('注册成功，重新登录')
                    else:
                        print('GEETEST验证失败')
                        self.browser.quit()
                    if count < 5:
                        count += 1
                    else:
                        cookie = None
                        return cookie
                else:
                    # 若只有一个window handle，则表明无需注册，登录已成功
                    print('登录成功')
                    self.browser.switch_to.window(self.browser.window_handles[0])
                    cookie = self.get_cookie()
                    self.browser.quit()
                    return cookie
        except Exception as ex:
            print(ex)
        self.browser.quit()   
        

if __name__ == '__main__':
    CookiesGenerate.main()



