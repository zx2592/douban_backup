"""
豆瓣登录认证模块

豆瓣登录页受滑块验证保护，表单提交式的账号密码登录已不再可用，
本模块只支持从浏览器导入的 Cookie 认证（见 import_cookies.py）。
"""
import json
import os
import requests
from config import DOUBAN_BASE_URL, HEADERS, DATA_DIR


class DoubanAuth:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.cookies_file = os.path.join(DATA_DIR, 'cookies.json')
        self.user_info_file = os.path.join(DATA_DIR, 'user_info.json')

    def login_with_cookies(self):
        """使用保存的 cookies 登录。这是唯一支持的认证方式。"""
        if not os.path.exists(self.cookies_file):
            print("[WARN] 未找到已保存的 Cookie 文件。")
            return False

        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
        except (OSError, json.JSONDecodeError) as error:
            print(f"[WARN] Cookie 文件无法读取（{error}），请重新导入。")
            return False

        if not isinstance(cookies, dict) or not cookies:
            print("[WARN] Cookie 文件内容为空或格式不正确，请重新导入。")
            return False

        self.session.cookies.update(cookies)

        if self._verify_login():
            print("[OK] 使用保存的 cookies 登录成功")
            self._save_user_info()
            return True

        print("[WARN] Cookie 已失效或已过期。")
        return False

    def _verify_login(self):
        """验证登录状态"""
        try:
            response = self.session.get(f"{DOUBAN_BASE_URL}/people/", timeout=30)
            return response.url != f"{DOUBAN_BASE_URL}/accounts/login"
        except Exception:
            return False

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
                print(f"[OK] 获取用户信息成功: {user_id} ({user_name})")
            else:
                print("[WARN] 无法获取用户 ID，请手动检查 cookies 是否包含有效登录信息。")

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
