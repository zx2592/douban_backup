"""
豆瓣爬虫基类
提供通用的爬取功能
"""
import time
import re
import json
from config import REQUEST_TIMEOUT, MAX_RETRIES, DELAY_BETWEEN_REQUESTS, HEADERS


class BaseCrawler:
    def __init__(self, session):
        self.session = session
        self.data = []

    def _make_request(self, url, retries=MAX_RETRIES):
        """发起HTTP请求，带重试机制"""
        for i in range(retries):
            try:
                time.sleep(DELAY_BETWEEN_REQUESTS)
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response
            except Exception as e:
                if i == retries - 1:
                    print(f"请求失败: {url}, 错误: {e}")
                time.sleep(2)
        return None

    def _parse_items(self, response, collection_type=None):
        """解析页面中的条目列表，子类需重写"""
        raise NotImplementedError

    def _get_pagination(self, response):
        """获取分页信息，子类需重写"""
        raise NotImplementedError

    def crawl(self, url, collection_type=None):
        """爬取数据"""
        self.data = []
        current_url = url

        while current_url:
            print(f"正在爬取: {current_url}")
            response = self._make_request(current_url)

            if response is None:
                break

            items = self._parse_items(response, collection_type)
            self.data.extend(items)
            print(f"  已获取 {len(items)} 条数据")

            current_url = self._get_pagination(response)

        return self.data

    def _extract_json_ld(self, html):
        """从页面提取JSON-LD结构化数据"""
        try:
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL)
            return [json.loads(match) for match in matches]
        except:
            return []

    def _clean_text(self, text):
        """清理文本内容"""
        if text:
            return text.strip().replace('\n', ' ').replace('\t', ' ')
        return ''
