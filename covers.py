"""封面图片本地下载。

只保存图片 URL 算不上完整的备份：豆瓣图床对外链有 Referer 校验，条目下架
或改版后旧图地址也会失效，等真需要时链接往往已经打不开。本模块把封面下载
到本地，让备份自身完整。

几个刻意的取舍：
- 文件名只用豆瓣 ID（纯数字）或 URL 摘要，绝不用条目标题。标题来自页面，
  带路径分隔符或 .. 时会写到目标目录之外。
- 只下载豆瓣自家图床的地址。cover 字段是从 HTML 里解析出来的，不加限制
  等于让页面内容决定程序去请求任意主机。
- 已经下载过的文件直接跳过，所以中断后重跑不会重复下载。
- 单张图片失败只记一笔，不影响整次备份——封面是附加内容，不该让它拖垮
  已经抓好的数据。
"""
import hashlib
import os
import re
import time
from urllib.parse import urlparse

from config import COVER_DOWNLOAD_DELAY, REQUEST_TIMEOUT

# 豆瓣图床域名。cover 来自页面解析，必须限定主机，避免被页面内容牵着去
# 请求任意地址。
ALLOWED_COVER_HOSTS = (
    'doubanio.com',
    'douban.com',
)

ALLOWED_SCHEMES = ('http', 'https')

# 从 URL 结尾识别扩展名，认不出来时按 jpg 存。
_EXTENSION_PATTERN = re.compile(r'\.(jpg|jpeg|png|webp|gif)$', re.IGNORECASE)
DEFAULT_EXTENSION = '.jpg'

COVERS_DIR_NAME = 'covers'


def is_allowed_cover_url(url):
    """只放行豆瓣图床上的 http(s) 地址。"""
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    host = (parsed.hostname or '').lower()
    return any(host == allowed or host.endswith('.' + allowed) for allowed in ALLOWED_COVER_HOSTS)


def cover_filename(item, url):
    """生成安全的文件名。

    优先用豆瓣 ID —— 它是纯数字，天然安全且稳定。没有 ID 时退回 URL 的
    SHA256 前缀。任何情况下都不使用条目标题：标题来自页面，可能含有 /
    或 .. 而把文件写到目标目录之外。
    """
    douban_id = str(item.get('douban_id') or '').strip()
    if not douban_id.isdigit():
        douban_id = hashlib.sha256(url.encode('utf-8')).hexdigest()[:16]

    match = _EXTENSION_PATTERN.search(urlparse(url).path or '')
    extension = f'.{match.group(1).lower()}' if match else DEFAULT_EXTENSION
    return f'{douban_id}{extension}'


class CoverDownloader:
    """把一次备份里的封面逐张下载到本地。"""

    def __init__(self, session, output_dir, delay=None, timeout=REQUEST_TIMEOUT):
        self.session = session
        self.covers_root = os.path.join(output_dir, COVERS_DIR_NAME)
        self.delay = COVER_DOWNLOAD_DELAY if delay is None else delay
        self.timeout = timeout
        self.stats = {'downloaded': 0, 'skipped': 0, 'failed': 0, 'rejected': 0}

    def download_all(self, data):
        """遍历备份数据下载全部封面，并把本地路径写回每个条目。

        返回统计字典。条目的 cover_path 记录相对于导出目录的路径，方便
        整个 data/backup 目录搬走后仍然对得上。
        """
        for category, collections in data.items():
            for collection, items in collections.items():
                for item in items:
                    self._download_one(category, item)

        total = self.stats['downloaded'] + self.stats['skipped']
        print(
            f"  封面: 新下载 {self.stats['downloaded']} 张，"
            f"已存在 {self.stats['skipped']} 张，"
            f"失败 {self.stats['failed']} 张，"
            f"跳过非豆瓣地址 {self.stats['rejected']} 个"
            f"（本地共 {total} 张）"
        )
        return self.stats

    def _download_one(self, category, item):
        url = (item.get('cover') or '').strip()
        if not url:
            return None

        if not is_allowed_cover_url(url):
            self.stats['rejected'] += 1
            return None

        category_dir = os.path.join(self.covers_root, category)
        filename = cover_filename(item, url)
        path = os.path.join(category_dir, filename)
        relative = os.path.join(COVERS_DIR_NAME, category, filename)

        # 已经下过就不再请求，中断后重跑因此是增量的。空文件视为上次没写完。
        if os.path.exists(path) and os.path.getsize(path) > 0:
            item['cover_path'] = relative
            self.stats['skipped'] += 1
            return relative

        os.makedirs(category_dir, exist_ok=True)
        try:
            if self.delay:
                time.sleep(self.delay)
            # 豆瓣图床校验 Referer，不带这个头会拿到 403。
            response = self.session.get(
                url,
                timeout=self.timeout,
                headers={'Referer': 'https://www.douban.com/'},
            )
            if getattr(response, 'status_code', 0) != 200 or not response.content:
                self.stats['failed'] += 1
                return None

            temp_path = f'{path}.part'
            with open(temp_path, 'wb') as file_obj:
                file_obj.write(response.content)
            os.replace(temp_path, path)
        except Exception as error:
            # 封面是附加内容，单张失败不该影响已经抓好的数据。
            print(f"[WARN] 封面下载失败 ({url}): {error}")
            self.stats['failed'] += 1
            return None

        item['cover_path'] = relative
        self.stats['downloaded'] += 1
        return relative
