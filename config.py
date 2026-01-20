# config.py
# 豆瓣配置

DOUBAN_BASE_URL = 'https://www.douban.com'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 爬虫设置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2

# 数据存储目录
DATA_DIR = 'data'

# 默认备份项目
BACKUP_ITEMS = {
    'movies': True,
    'books': True,
    'music': True,
    'games': True
}
