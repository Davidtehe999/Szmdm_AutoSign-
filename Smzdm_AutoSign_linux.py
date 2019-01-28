from selenium import webdriver
import re
from PIL import Image
from urllib.request import urlopen
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import sys
import random
import time
import json


class Smzdm():
    #初始化
    def __init__(self,myUserName,myPassWord,url,is_headless):
        chromeOptions = Options()
        self.myUserName = myUserName
        self.myPassWord = myPassWord
        self.url = url
        self.browser = webdriver.Chrome(executable_path="./chromedriver")
        self.wait = WebDriverWait(self.browser, 20)
        if is_headless:
            chromeOptions.add_argument('--headless')
            chromeOptions.add_argument("--start-maximized")
            # 谷歌文档提到需要加上这个属性来规避bug
            chromeOptions.add_argument('--disable-gpu')
            # 设置屏幕器宽高
            chromeOptions.add_argument("--window-size=1440,750")
            #设置沙盒模式，在无gui的环境中非常重要！！！！
            chromeOptions.add_argument("--no-sandbox")


    def login(self):
        #self.browser.set_page_load_timeout(20)
        #self.browser.set_script_timeout(20)
        try:
            self.browser.get(self.url)

        except:
            print("Loading timeout, pass...")
            self.browser.execute_script("window.stop()")
            print("执行停止")
            pass


        #尝试用cookies登陆
        try:
            # 加入cookies
            self.login_with_cookie()
            time.sleep(5)
        except:
            pass



        #判断cookies是否过期,方法为检测登陆用户名，如果是"Hi  你好"则登陆失败
        signClick = self.browser.find_element_by_class_name("old-entry")
        loginState = self.browser.find_element_by_class_name("user-name").text
        #登陆失败则重新登陆，过geetest，并且保存最新的cookie
        #if signClick.text == "签到得积分":
        if loginState == "Hi  你好":
            print("cookies登陆失败，开始过验证登陆")
            signClick.click()
            self.browser.implicitly_wait(5.7)
            time.sleep(3)

            #跳转到登陆的frame
            self.browser.switch_to.frame("J_login_iframe")

            userName = self.browser.find_element_by_id("username")
            passWord = self.browser.find_element_by_id("password")
            submit = self.browser.find_element_by_id("login_submit")
            userName.send_keys(self.myUserName)
            time.sleep(0.5)
            passWord.send_keys(self.myPassWord)
            time.sleep(0.88)
            submit.click()

            #有缺口的被打乱成52块的验证图在网页的位置
            gt_cut_bg = "//div[@class='gt_cut_bg gt_show']/div"
            #有缺口的被打乱成52块的验证图即将在本地保存的文件名
            img_file_name_0 = "./images/smzdm/cut_bg.jpg"
            #把被打乱的验证图根据网页提供坐标还原为正常的图
            cut_bg = self.get_img(gt_cut_bg, img_file_name_0)

            #完整的被打乱成52块的验证图在网页的位置
            get_cut_fullbg_slice = "//div[@class='gt_cut_fullbg gt_show']/div"
            #完整的被打乱成52块的验证图即将在本地保存的文件名
            img_file_name_1 = "./images/smzdm/cut_fullbg_slice.jpg"
            # 把被打乱的验证图根据网页提供坐标还原为正常的图
            cut_fullbg_slice = self.get_img(get_cut_fullbg_slice, img_file_name_1)

            #计算缺口位置的x坐标
            loc_x = self.get_gap(cut_bg, cut_fullbg_slice)

            #移动
            self.move_to_gap(loc_x)

            time.sleep(5)






    def get_img(self, img_xpath, img_file_name):
        #通过网页位置将被打乱为52块的图的html/css信息读取到image_divs
        image_divs = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, img_xpath)))
        #得到完整的被打乱的图的坐标并把里面的后缀webp换成jpg
        imageurl = re.findall(r'background-image: url\("(.*)"\);',
                              image_divs[0].get_attribute("style"))[0].replace("webp", "jpg")
        #把完整的被打乱的图保存在本地，文件名img_file_name
        with open(img_file_name, 'wb') as f:
            img = urlopen(imageurl).read()
            f.write(img)

        #把被打乱的图的被一小块的坐标按顺序梳理为location_list
        location_list = []
        for image in image_divs:
            locaion = {}
            loc_find = re.findall(r"background-position: (.*?)px (.*?)px;", image.get_attribute("style"))

            locaion['x'] = int(loc_find[0][0])
            locaion['y'] = int(loc_find[0][1])
            location_list.append(locaion)
        # print(location_list)
        image_new = self.get_merge_image(img_file_name, location_list)
        return image_new

    def get_merge_image(self, img_file_name, location_list):
        im = Image.open(img_file_name)
        im_list_upper = []
        im_list_down = []

        # 根据52个div的x和y坐标，进行循环，把打乱了的图切割成52个小图片
        for location in location_list:
            if location['y'] == -58:
                # 宽度==10
                # print((abs(location['x']), 58, abs(location['x']) + 10, 116))
                im_list_upper.append(im.crop((abs(location['x']), 58, abs(location['x']) + 10, 116)))
            elif location['y'] == 0:
                im_list_down.append(im.crop((abs(location['x']), 0, abs(location['x']) + 10, 58)))

        # 建立一个新的图片
        new_im = Image.new('RGB', (260, 116))

        x_offset = 0
        # 根据下图片列表，把小图片按照 x和y坐标，粘贴到 new_im
        for im in im_list_upper:
            new_im.paste(im, (x_offset, 0))
            x_offset += im.size[0]

        x_offset = 0
        # 根据下图片列表，把小图片按照 x和y坐标，粘贴到 new_im
        for im in im_list_down:
            new_im.paste(im, (x_offset, 58))
            x_offset += im.size[0]


        new_im.save(img_file_name.replace(".jpg", "_merge.jpg"))
        return new_im

    def is_pixel_equal(self, image1, image2, x, y):
        '''
        判断两个像素是否相同
        :param image1:
        :param image2:
        :param x:
        :param y:
        :return:
        '''

        # 取两个图片的像素点
        threshold = 55
        pixel1 = image1.getpixel((x, y))
        pixel2 = image2.getpixel((x, y))
        # print(pixel1)
        # print(pixel2)

        for i in range(0, 3):
            if abs(pixel1[i] - pixel2[i]) >= threshold:
                # print(abs(pixel1[i] - pixel2[i]))
                return False

        return True

    def get_gap(self, image1, image2):
        '''
        获取缺口的起始位置
        :param image1: 不带缺口图片
        :param image2: 带缺口图片
        :return:
        '''
        x = 0
        for x in range(0, 260):
            for y in range(0, 116):

                if not self.is_pixel_equal(image1, image2, x, y):
                    # 返回第一像素不同的位置 x的坐标 即 滑块开始的地方至缺口x位置
                    print("GAP is:", x)
                    return x


    def get_track(self, distance):
        '''
        根据偏移量获取以哦对那个轨迹
        先做匀加速运动  后匀减速运动
        :param distance:
        :return: 移动轨迹
        '''
        # 滑块起始位置与图片边缘有点点距离差距 可做点调整
        distance -= 0
        track = []
        current = 0
        mid = distance * 4 / 5
        t = 0.2
        v = 0
        while current < distance:
            if current < mid:
                a = random.uniform(4, 5.3)
            else:
                a = random.uniform(0,-2.9)

            v0 = v
            v = v0 + a * t
            move = v0 * t + 1 / 2 * a * t * t
            current += move
            track.append(round(move))
            #track.append(move)

        # 上面的算法整个track[]之和会与distance有误差（因最后一次while判断），下面是排除误差
        sumDistance = sum(track)
        errorDistance = round((distance - sumDistance), 3)
        track.append(errorDistance)


        return track

    def move_to_gap(self, distance):
        '''
        拖动滑块到缺口处
        :return:
        '''
        #tracks = self.get_track(distance + 20)

        # 模拟人的拖动，第一阶段拖动滑块超过缺口exceedDistance
        exceedDistance = round(random.uniform(10, 20), 2)
        tracks = self.get_track(distance + exceedDistance)
        print("Distance:", distance)
        print("exceedDistance:", exceedDistance)
        print("SumTrack:", sum(tracks))
        #第二阶段滑块往回拖
        tracks_back = []
        #back = self.get_track(20.1)
        back = self.get_track(exceedDistance)
        for i in back:
            tracks_back.append(i*(-1))
        tracks_back.append((-4.5))


        # 滑块
        slider_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='gt_slider_knob gt_show']")))

        # 移动
        ActionChains(self.browser).click_and_hold(slider_button).perform()
        for x in tracks:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        for x in tracks_back:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)

        #模拟人的拖动，前后随机犹豫xoffset
        hesitateDistance = round(random.uniform(0,3.5),1)
        #ActionChains(self.browser).move_by_offset(xoffset=3.5, yoffset=0).perform()
        ActionChains(self.browser).move_by_offset(xoffset=hesitateDistance, yoffset=0).perform()
        time.sleep(0.7)
        #ActionChains(self.browser).move_by_offset(xoffset=-3.5, yoffset=0).perform()
        ActionChains(self.browser).move_by_offset(xoffset=(hesitateDistance*(-1)+0.113), yoffset=0).perform()
        time.sleep(0.3)

        ActionChains(self.browser).release().perform()

    def auto_sign(self):
        self.browser.implicitly_wait(10)

        #从登陆的frame跳转回主内容
        self.browser.switch_to.default_content()

        #签到按钮
        sign = self.browser.find_element_by_class_name("J_punch")
        signState = self.browser.find_element_by_class_name("user-name").text
        time.sleep(10)

        if signState != "Hi  你好":#登陆成功

            if sign.text == "签到领奖":

                #print("点击签到领奖按钮")
                sign.click()
                #print("clicked")
                time.sleep(5)
                sign_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print("smzdm签到成功")
            else:
                sign_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

                print(sign_time)
                print("已经签到")

            self.get_cookie()
            print("过验证成功，保存最新的cookies")
        elif signState == "Hi  你好":#登陆不成功
            print("登陆失败，重新登陆")
            raise RuntimeError("过geetest失败")#强制让程序出错，重新try

        self.browser.quit()

    #得到cookie
    def get_cookie(self):
        #get_cookies()方法得到的是所有的cookies，是一个list
        cookies = smzdm.browser.get_cookies()
        # 用dumps()将这个元素变成双引号,type为str，只有str可以保存在txt
        cookies = json.dumps(cookies)
        #保存
        f = open("./smzdm_" + str(self.myUserName)+"_cookie.txt", "w")
        f.write(cookies)

    #用cookie登陆
    def login_with_cookie(self):
        cookie = open("./smzdm_" + str(self.myUserName)+"_cookie.txt").read()
        #用json.loads()把str变成dict
        cookie = json.loads(cookie)

        for i in cookie:
            self.browser.add_cookie(i)
        self.browser.refresh()

'''
#发送邮件提醒
class mailToMe():
    def __init__(self,mailAdd, mailPWD, sendTo):
        '''



if(__name__=="__main__"):
    #实例的参数依次是用户名/密码/网址/是否无头（False为否，True为是)
    while(1):
        try:
            smzdm = Smzdm("username", "password", "http://www.smzdm.com", False)
            smzdm.login()
            time.sleep(5)
            smzdm.auto_sign()
            time.sleep(5)
            break
        except:
            print("错误：", sys.exc_info())
            smzdm.browser.quit()
            print("退出浏览器")



