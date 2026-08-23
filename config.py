# config.py
# 豆瓣配置

import os

DOUBAN_BASE_URL = 'https://www.douban.com'
APP_VERSION = '1.8'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 爬虫设置
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
DELAY_BETWEEN_REQUESTS = 2

# 封面走的是图床，比正文页面宽松得多，间隔可以短一些；
# 否则上千张封面按 2 秒一张要跑半个多小时。
COVER_DOWNLOAD_DELAY = 0.5

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_data_dir():
    """决定 Cookie 和备份文件的存放位置。

    从仓库直接运行时用项目下的 data/：这是一直以来的行为，路径相对于模块
    而不是当前工作目录，所以在哪儿敲命令都一样。

    但 pip 安装之后模块位于 site-packages，再往那里写就不合适了——升级会
    被一并清掉，有些环境下那里还是只读的，用户也很难找到自己的备份。这种
    情况改用主目录下的 ~/.douban_backup。

    DOUBAN_BACKUP_HOME 可以覆盖上述判断。
    """
    override = os.environ.get('DOUBAN_BACKUP_HOME')
    if override:
        return os.path.abspath(os.path.expanduser(override))

    # 这两个标记只存在于源码检出，安装到 site-packages 后不会有。
    for marker in ('pyproject.toml', '.git'):
        if os.path.exists(os.path.join(PROJECT_DIR, marker)):
            return os.path.join(PROJECT_DIR, 'data')

    return os.path.join(os.path.expanduser('~'), '.douban_backup')


DATA_DIR = _resolve_data_dir()

# 默认备份项目
BACKUP_ITEMS = {
    'movies': True,
    'books': True,
    'music': True,
    'games': True,
    # 长评列表每页 10 篇，通常只有几页，代价很小；
    # 抓取完整正文另需每篇一次请求，所以放在 --full-reviews 后面。
    'reviews': True,
}
