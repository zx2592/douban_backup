"""
豆瓣爬虫基类
提供通用的爬取功能
"""
import time
import re
import json
from config import REQUEST_TIMEOUT, MAX_RETRIES, DELAY_BETWEEN_REQUESTS, HEADERS
from bs4 import BeautifulSoup

from diagnostics import classify_response, describe_empty_parse, is_known_empty_page


class BaseCrawler:
    PAGE_SIZE = 15
    RETRYABLE_RESPONSE_CODES = {"rate_limited", "server_error"}

    def __init__(
        self,
        session,
        category_key=None,
        state_store=None,
        request_delay=DELAY_BETWEEN_REQUESTS,
    ):
        self.session = session
        self.data = []
        self.category_key = category_key
        self.state_store = state_store
        self.request_delay = (
            DELAY_BETWEEN_REQUESTS if request_delay is None else request_delay
        )
        self.incomplete = False

    def _make_request(self, url, retries=MAX_RETRIES):
        """发起HTTP请求，带重试机制"""
        for i in range(retries):
            try:
                time.sleep(self.request_delay)
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                status, code, message = classify_response(response)
                if status == "ok" or code not in self.RETRYABLE_RESPONSE_CODES:
                    return response
                if i == retries - 1:
                    return response
                print(f"[WARN] {message} 即将重试（{i + 1}/{retries}）")
            except Exception as e:
                if i == retries - 1:
                    print(f"[ERROR] 请求失败: {url}, 错误: {e}")
                    return None
            if i < retries - 1:
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
        visited_urls = set()

        while current_url:
            if current_url in visited_urls:
                print("[WARN] 分页链接发生循环，已停止并保留断点。")
                self.incomplete = True
                break
            visited_urls.add(current_url)

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
                self.incomplete = True
                break

            status, _, message = classify_response(response)
            if status != 'ok':
                print(f"[WARN] {message}")
                self.incomplete = True
                break

            data_before_page = list(self.data)
            items = self._parse_items(response, collection_type)
            self.data.extend(items)
            print(f"  已获取 {len(items)} 条数据")

            next_url = self._get_pagination(response)
            page_complete = self._is_last_page(response, items)

            if not items and next_url is None:
                empty_message = describe_empty_parse(response)
                print(f"[WARN] {empty_message}")
                page_complete = is_known_empty_page(response)

            if next_url and next_url in visited_urls:
                print("[WARN] 下一页链接指向已抓取页面，已停止并保留断点。")
                self.data = data_before_page
                self.incomplete = True
                break

            if self.state_store and self.category_key:
                if next_url:
                    self.state_store.update_progress(
                        self.category_key,
                        collection_type,
                        current_url=current_url,
                        next_url=next_url,
                        items=self.data,
                    )
                elif page_complete:
                    self.state_store.mark_complete(
                        self.category_key,
                        collection_type,
                        self.data,
                    )

            if next_url is None and not page_complete:
                print("[WARN] 无法确认已经到达最后一页，已停止并保留当前页断点。")
                if self.state_store and self.category_key:
                    self.data = data_before_page
                self.incomplete = True
                break

            current_url = next_url

        return self.data

    def _is_last_page(self, response, items):
        """仅在有明确页面证据时确认分页结束。"""
        soup = BeautifulSoup(response.text, 'html.parser')
        next_container = soup.select_one('span.next')
        if next_container is not None:
            return next_container.select_one('a') is None
        return 0 < len(items) < self.PAGE_SIZE

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
