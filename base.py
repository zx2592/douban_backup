"""
豆瓣爬虫基类
提供通用的爬取功能
"""
import time
import re
import json
from config import REQUEST_TIMEOUT, MAX_RETRIES, DELAY_BETWEEN_REQUESTS, HEADERS
from diagnostics import classify_response, describe_empty_parse


class BaseCrawler:
    def __init__(self, session, category_key=None, state_store=None):
        self.session = session
        self.data = []
        self.category_key = category_key
        self.state_store = state_store

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
                    print(f"[ERROR] 请求失败: {url}, 错误: {e}")
                time.sleep(2)
        return None

    def _parse_items(self, response, collection_type=None):
        """解析页面中的条目列表，子类需重写"""
        raise NotImplementedError

    def _get_pagination(self, response):
        """获取分页信息，子类需重写"""
        raise NotImplementedError

    def crawl_collection(self, url, collection_type=None):
        initial_data = []
        start_url = url

        if self.state_store and self.category_key:
            if self.state_store.is_collection_complete(self.category_key, collection_type):
                return self.state_store.get_partial_items(self.category_key, collection_type)

            initial_data = self.state_store.get_partial_items(self.category_key, collection_type)
            start_url = self.state_store.get_resume_url(self.category_key, collection_type) or url

            if initial_data or start_url != url:
                print(f"[RESUME] 从断点继续: {self.category_key}/{collection_type}")

        return self.crawl(start_url, collection_type, initial_data=initial_data)

    def crawl(self, url, collection_type=None, initial_data=None):
        """爬取数据"""
        self.data = list(initial_data or [])
        current_url = url

        while current_url:
            print(f"正在爬取: {current_url}")
            if self.state_store and self.category_key:
                self.state_store.update_progress(
                    self.category_key,
                    collection_type,
                    current_url=current_url,
                    next_url=current_url,
                    items=self.data,
                )
            response = self._make_request(current_url)

            if response is None:
                break

            status, _, message = classify_response(response)
            if status != 'ok':
                print(f"[WARN] {message}")
                break

            items = self._parse_items(response, collection_type)
            self.data.extend(items)
            print(f"  已获取 {len(items)} 条数据")

            next_url = self._get_pagination(response)
            if not items and next_url is None:
                print(f"[WARN] {describe_empty_parse(response)}")

            if self.state_store and self.category_key:
                if next_url:
                    self.state_store.update_progress(
                        self.category_key,
                        collection_type,
                        current_url=current_url,
                        next_url=next_url,
                        items=self.data,
                    )
                else:
                    self.state_store.mark_complete(
                        self.category_key,
                        collection_type,
                        self.data,
                    )

            current_url = next_url

        return self.data

    def _extract_json_ld(self, html):
        """从页面提取JSON-LD结构化数据"""
        try:
            pattern = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.findall(pattern, html, re.DOTALL)
            return [json.loads(match) for match in matches]
        except Exception:
            return []

    def _clean_text(self, text):
        """清理文本内容"""
        if text:
            return text.strip().replace('\n', ' ').replace('\t', ' ')
        return ''
