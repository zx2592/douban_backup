"""
豆瓣登录认证模块
支持账号密码登录和cookies登录
"""
import json
import os
import time
import requests
from config import DOUBAN_BASE_URL, HEADERS, DATA_DIR


class DoubanAuth:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cookies_file = os.path.join(DATA_DIR, 'cookies.json')
        self.user_info_file = os.path.join(DATA_DIR, 'user_info.json')

    def login_with_cookies(self):
        """使用保存的cookies登录"""
        if os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            self.session.cookies.update(cookies)

            if self._verify_login():
                print("✓ 使用保存的cookies登录成功")
                self._save_user_info()
                return True

        return False

    def login(self, email=None, password=None):
        """账号密码登录"""
        if not email or not password:
            print("请提供豆瓣账号和密码")
            return False

        login_url = f"{DOUBAN_BASE_URL}/people/"
        self.session.get(login_url, timeout=30)

        captcha_url = f"{DOUBAN_BASE_URL}/misc/id"
        params = {'type': 'login'}
        try:
            captcha = self.session.get(captcha_url, params=params, timeout=30)
            captcha_id = captcha.json().get('id')
            if captcha_id:
                print(f"检测到验证码ID: {captcha_id}")
        except Exception as e:
            captcha_id = None
            print(f"获取验证码失败: {e}")

        login_data = {
            'ck': '',
            'remember': 'on',
            'redir': 'https://www.douban.com/',
            'form_email': email,
            'form_password': password,
        }

        if captcha_id:
            login_data['captcha_id'] = captcha_id
            print("已包含验证码ID")

        login_post_url = f"{DOUBAN_BASE_URL}/accounts/login"
        response = self.session.post(login_post_url, data=login_data, timeout=30)

        print(f"登录响应URL: {response.url}")

        if response.url == 'https://www.douban.com/' or 'douban.com/people' in response.url:
            print("✓ 登录成功")
            self._save_cookies()
            self._save_user_info()
            return True

        print("登录失败，请检查账号密码或验证码")
        return False

    def _verify_login(self):
        """验证登录状态"""
        try:
            response = self.session.get(f"{DOUBAN_BASE_URL}/people/", timeout=30)
            return response.url != f"{DOUBAN_BASE_URL}/accounts/login"
        except:
            return False

    def _save_cookies(self):
        """保存cookies到文件"""
        cookies = self.session.cookies.get_dict()
        with open(self.cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False)

    def _save_user_info(self):
        """保存用户信息"""
        try:
            # 访问个人主页自动跳转
            # /mine/ usually redirects to /people/<id>/
            response = self.session.get(f"{DOUBAN_BASE_URL}/mine/", timeout=30, allow_redirects=True)
            
            import re
            # Check url first
            user_id = None
            match = re.search(r'people/([^/]+)/', response.url)
            if match:
                user_id = match.group(1)
            
            # If standard URL match failed, look for id in page content or other indicators
            # But usually /mine/ -> /people/id/
            
            user_name = None
            name_match = re.search(r'<div class="info">.*?<h1>(.*?)</h1>', response.text, re.DOTALL) # Profile page h1
            if not name_match:
                 name_match = re.search(r'<span class="pl">(.*?)</span>', response.text) # Nav or side
            
            if name_match:
                user_name = name_match.group(1).strip()

            if user_id:
                user_info = {'id': user_id}
                if user_name:
                    user_info['name'] = user_name
                
                with open(self.user_info_file, 'w', encoding='utf-8') as f:
                    json.dump(user_info, f, ensure_ascii=False)
                print(f"✓ 获取用户信息成功: {user_id} ({user_name})")
            else:
                print("⚠ 无法获取用户ID，请手动检查 cookies 是否包含有效登录信息。")

        except Exception as e:
            print(f"获取用户信息失败: {e}")

    def get_session(self):
        """获取已登录的session"""
        return self.session

    def load_cookies(self):
        """加载cookies"""
        if os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            self.session.cookies.update(cookies)
            return True
        return False
