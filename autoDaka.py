# -*- coding: utf-8 -*-
# /usr/bin/python

"""
BUAA AutoDaka Program
Version: 1.1
Date: 2020.08.25 20:30
"""

import datetime
import logging
import re
import time
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

import json
import requests

# 健康打卡平台的 url
login_url = "https://app.buaa.edu.cn/uc/wap/login?redirect=https%3A%2F%2Fapp.buaa.edu.cn%2Fncov%2Fwap%2Fdefault%2Findex"
base_url = "https://app.buaa.edu.cn/ncov/wap/default/index"
save_url = "https://app.buaa.edu.cn/ncov/wap/default/save"
login_check_url = "https://app.buaa.edu.cn/uc/wap/login/check"
save_geo_url = "https://app.buaa.edu.cn/ncov/wap/default/save-geo-error"

# PC小程序抓包获取的 user-Agent
userAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36 MicroMessenger/7.0.9.501 NetType/WIFI MiniProgramEnv/Windows WindowsWechat"
headers = {'User-Agent': userAgent}

# 创建日志系统
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    level=logging.INFO,
                    filename='Daka.log',
                    filemode='a')

# 第三方 SMTP 邮件服务
mail_host = "smtp.163.com"
mail_sender = 'xxxx@163.com'  # 你的邮箱
mail_pass = 'xxxx'  # 你的授权码


class Daka(object):
    def __init__(self, username, password, mail):
        self.username = username
        self.password = password
        self.name = ""
        self.number = ""
        self.mail = mail
        self.html = ""
        self.geoInfo = ""
        self.info = ""
        self.session = requests.Session()

    def sendMail(self, flag):
        """Send mail to remind users"""
        if flag:
            subjects = "自动打卡成功！"
        else:
            subjects = "自动打卡失败！"
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msg = "{}: 时间：{}，{}".format(self.username, now, subjects)
        message = MIMEText(msg, 'plain', 'utf-8')
        message['From'] = formataddr(["autoDaka", mail_sender])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        message['To'] = formataddr([self.username, self.mail])
        message['Subject'] = subjects  # 邮件的主题

        try:
            server = smtplib.SMTP_SSL(mail_host, 465)  # 发件人邮箱中的SMTP服务器
            server.login(mail_sender, mail_pass)  # 括号中对应的是发件人邮箱账号、邮箱密码
            server.sendmail(mail_sender, self.mail, message.as_string())
            logging.info("{} 邮件发送成功 to {}".format(self.username, self.mail))
            server.quit()  # 关闭连接
        except Exception as err:
            logging.error("{} 无法发送邮件，原因：{}".format(self.username, str(err)))
        finally:
            return

    def login(self):
        """Login to BUAA platform"""
        for i in range(10):  # 循环请求，直到成功
            try:
                res = self.session.get(login_url, headers=headers)
                if res and res.status_code == 200:
                    break
            except Exception as err:  # 奇奇怪怪的异常（例如开代理了就会抛 SSLError）
                logging.warning("{} 登陆平台打开失败,第{}次，失败原因-{}".format(self.username, i, err))
                time.sleep(1)
                if i == 9:
                    logging.error('登陆平台多次打开失败！')
                    return False

        time.sleep(1)

        data = {
            'username': self.username,
            'password': self.password,
        }
        for i in range(10):
            try:
                res = self.session.post(url=login_check_url, data=data, headers=headers)
                resJson = json.loads(res.content.decode())  # 格式  {"e":0,"m":"操作成功","d":{}}
                if resJson['e'] == 0:
                    logging.info("{} 登陆成功".format(self.username))
                    break
                else:
                    raise LoginResError(resJson['m'])
            except Exception as err:
                logging.warning("{} 登陆失败，第{}次，原因-{},".format(self.username, i, str(err)))
                time.sleep(1)
                if i == 9:
                    logging.error('登录操作多次失败！')
                    return False
        return True

    def postInfo(self):
        """Post the hitCard info"""
        for i in range(10):
            try:
                res = self.session.post(save_url, data=self.info, headers=headers)
                if res.status_code == 200:
                    logging.info("{} 提交 info 成功。返回报文：{}".format(self.username, res.text))
                    break
            except Exception as err:
                logging.warning("{} 提交 info 失败,第{}次，失败原因-{}".format(self.username, i, str(err)))
                time.sleep(1)
                if i == 9:
                    logging.error("多次提交 info 失败！")
                    return False
        return True

    def postGeoInfo(self):
        """Post geo_api_info"""
        for i in range(10):
            try:
                res = self.session.post(save_geo_url, data=self.geoInfo, headers=headers)
                if res.status_code == 200:
                    logging.info("{} 提交 geo_api_info 成功。返回报文：{}".format(self.username, res.text))
                    break
            except Exception as err:
                logging.warning("{} 提交 geo_api_info 失败,第{}次，失败原因-{}".format(self.username, i, str(err)))
                time.sleep(1)
                if i == 9:
                    logging.error("多次提交 geo_api_info 失败！")
                    return False
        return True

    def getHtml(self):
        """Get hitCard info, which is the old info with updated new time and id."""
        for i in range(10):
            try:
                res = self.session.get(base_url, headers=headers)
                if res.status_code == 200:
                    logging.info("{} 获取填写页面成功".format(self.username))
                    html = res.content.decode()
                    self.html = html
                    return True
            except Exception as err:
                logging.warning("{} 获取填写页面失败,第{}次,错误原因-{}".format(self.username, i, str(err)))
                time.sleep(1)
                if i == 9:
                    logging.error('多次获取填写页面失败！')
                    return False

    def hasFlag(self):
        """Check whether you hit card today"""
        try:
            hasFlag = re.findall(r'hasFlag: \'(.)', self.html)[0]
            if hasFlag == '1':  # 填写页面前端也是根据 hasFlag == 1 来提示今日已提交
                return 1
        except IndexError as err:
            logging.error("{} 正则表达式匹配 hasFlag 错误！请联系作者。错误信息：{}".format(self.username, str(err)))
            return -1
        return 0

    def getDate(self):
        """Get current date"""
        today = datetime.date.today()
        return "%4d%02d%02d" % (today.year, today.month, today.day)

    def getInfo(self):
        """Get hitCard info, which is the old info with updated new time and id."""
        # 从 html 中获取 old_info 与 new_info 与个人信息
        try:
            old_info = json.loads(re.findall(r'oldInfo: ({[^\n]+})', self.html)[0])  # 获取 old_info
            new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', self.html)[0])  # 获取 def
            geo_api_info_raw = old_info['geo_api_info']
            geo_api_info_json = json.loads(geo_api_info_raw)  # 获取 old_info 中的 geo_api_info
            name = re.findall(r'realname: "([^\"]+)",', self.html)[0]  # 姓名和学号，没必要
            number = re.findall(r"number: '([^\']+)',", self.html)[0]
        except IndexError as err:
            logging.error("{} 正则表达式匹配 info 错误！请联系作者。错误信息：{}".format(self.username, str(err)))
            return False
        except json.decoder.JSONDecodeError as err:
            logging.error("{} info json 错误！请联系作者。错误信息：{}".format(self.username, str(err)))
            return False

        self.name = name
        self.number = number

        # 稍微处理一下 geo_api_info
        # 可以设置 GPS 数据浮动
        # 手机微信访问一下下列网址获得详细信息：https://lbs.amap.com/api/javascript-api/example/location/browser-location/
        geo_api_info_json['isConverted'] = 'true'  # python 会把这个弄成 True
        # geo_api_info_json['accuracy'] = 40  # 这是精度，手机30-40？
        # position_temp = geo_api_info_json['position']  # 这是经纬度
        # 'position': {'Q': x, 'R': x, 'lng': x, 'lat': x}

        # 把 oldInfo 里的 geo_api_info 处理为 json
        old_info['geo_api_info'] = geo_api_info_json
        self.geoInfo = geo_api_info_json
        logging.info("{} 获取 geo_api_info 成功。geo_api_info: {}".format(self.username, self.geoInfo))

        # 替换 old_info 的 created、id、date，作为 new_info
        new_info = old_info.copy()
        new_info['id'] = new_info_tmp['id']
        new_info['created'] = round(time.time())
        new_info['date'] = self.getDate()

        # 几个奇怪的参数从 def 中加进去
        # new_info.update({"gwszdd": ""})
        # new_info.update({"sfyqjzgc": ""})
        # new_info.update({"jrsfqzys": ""})
        # new_info.update({"jrsfqzfy": ""})
        for key in new_info_tmp:
            if key not in new_info:
                new_info[key] = new_info_tmp[key]

        self.info = new_info
        logging.info("{} 获取 info 成功。info: {}".format(self.username, self.info))
        return True

    def autoDaka(self):
        """Hit card process"""
        logging.info("{} 开始打卡".format(self.username))

        # 登录
        flag = self.login()
        if not flag:
            return -1

        time.sleep(1)

        # 获取页面
        flag = self.getHtml()
        if not flag:
            return -1

        # 判断是否已打卡
        hasFlag = self.hasFlag()
        if hasFlag == 1:
            logging.info("{} 已打卡，无需执行操作".format(self.username))
            return 0
        elif hasFlag == -1:
            return -1

        # 获取 info
        flag = self.getInfo()
        if not flag:
            return -1

        # 提交 geo_api_info
        flag = self.postGeoInfo()
        if not flag:
            return -1

        time.sleep(1)

        # 提交 info
        flag = self.postInfo()
        if not flag:
            return -1

        time.sleep(1)

        # 重新访问，验证是否成功
        if not self.getHtml():
            return -1
        hasFlag = self.hasFlag()
        if hasFlag:
            logging.info("{} 打卡成功".format(self.username))
            return 1
        logging.warning("{} 打卡失败".format(self.username))
        return -1


class LoginResError(Exception):
    """
    Login Request success but Return Exception
    For Example, Password Error
    """
    pass


def autoDaka(username, password, mail):
    dk = Daka(username, password, mail)
    flag = dk.autoDaka()
    if flag == 0:
        return True
    if flag == 1:
        dk.sendMail(True)
        return True
    logging.error("{} 打卡失败，再次尝试".format(username))
    flag = dk.autoDaka()
    if flag == 0:
        return True
    if flag == 1:
        dk.sendMail(True)
        return True
    logging.error("{} 再次打卡失败，发送邮件提醒".format(username))
    dk.sendMail(False)
    return False


def getUsersToDaka():
    users = open('user.json', 'r', encoding='UTF-8').read()
    usersJson = json.loads(users)
    lens = len(usersJson)
    success = ""
    fail = ""
    for i in range(0, lens):
        flag = autoDaka(usersJson[i]['username'], usersJson[i]['password'], usersJson[i]['mail'])
        if flag:
            success = "{} {}".format(success, usersJson[i]['username'])
        else:
            fail = "{} {}".format(fail, usersJson[i]['username'])
        time.sleep(1)
    logging.info("打卡成功：{}".format(success))
    logging.info("打卡失败：{}".format(fail))
    logging.info("本次打卡结束\n")


if __name__ == "__main__":
    getUsersToDaka()
