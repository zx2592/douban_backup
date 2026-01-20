"""
Import Cookies for Douban Backup
由于豆瓣登录增加了复杂的验证码机制，建议使用此脚本导入浏览器Cookies
"""
import json
import os
from config import DATA_DIR
import requests
from config import HEADERS

def parse_cookies(cookie_str):
    """解析Cookie字符串为字典"""
    cookies = {}
    for item in cookie_str.split(';'):
        if '=' in item:
            name, value = item.strip().split('=', 1)
            cookies[name] = value
    return cookies

def save_cookies(cookies):
    """保存Cookies到文件"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    filepath = os.path.join(DATA_DIR, 'cookies.json')
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, ensure_ascii=False)
    print(f"✓ Cookies 已保存到: {filepath}")

def verify_cookies(cookies):
    """验证Cookies是否有效"""
    print("正在验证 Cookies...")
    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(cookies)
    
    try:
        response = session.get('https://www.douban.com/mine/', timeout=10, allow_redirects=False)
        if response.status_code == 200 or response.status_code == 302:
            # Check if redirected to login
            if 'accounts/login' in response.headers.get('Location', ''):
                return False
            return True
    except Exception as e:
        print(f"验证出错: {e}")
    return False

def main():
    print("=" * 50)
    print("豆瓣 Cookies 导入工具")
    print("=" * 50)
    print("说明: 由于豆瓣登录保护升级，请在浏览器登录后复制 Cookie 导入。")
    print("1. 在浏览器(Chrome/Edge)打开 https://www.douban.com 并登录")
    print("2. 按 F12 打开开发者工具 -> Network (网络) 标签页")
    print("3. 刷新页面，点击第一个请求 (www.douban.com)")
    print("4. 在 Request Headers (请求头) 中找到 'Cookie' 字段")
    print("5. 复制 'Cookie' 冒号后的所有内容")
    print("-" * 50)
    
    cookie_str = input("请粘贴 Cookie 内容: ").strip()
    
    if not cookie_str:
        print("未输入内容!")
        return
        
    cookies = parse_cookies(cookie_str)
    
    if verify_cookies(cookies):
        save_cookies(cookies)
        print("\n成功! 现在可以直接运行 python main.py 进行备份了。")
    else:
        print("\n警告: 验证失败。输入的 Cookies 可能无效或已过期。")
        save = input("仍要保存吗? (y/n): ")
        if save.lower() == 'y':
            save_cookies(cookies)

if __name__ == '__main__':
    main()
