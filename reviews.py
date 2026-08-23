"""长评（影评/书评/乐评/游戏评）备份。

短评只有一句话，长评却是真正花时间写出来的东西，此前完全没有备份。

与其他分类的两点不同：
- 长评没有"想看/在看/看过"这类状态，所以只用一个伪收藏夹 collect。这样
  既能复用 BaseCrawler 的翻页、重试、断点和增量，也能直接套用导出逻辑。
- 列表页只给出正文摘要。完整正文要逐篇打开评论页，代价是每篇一次请求，
  因此放在 --full-reviews 后面，默认只抓摘要。

页面结构说明：豆瓣的长评列表用过好几套标记，这里对标题、正文、评分、
被评对象都准备了多个候选选择器。万一豆瓣再次改版，diagnostics 会给出
"未解析到条目，可能是页面结构发生了变化"的提示，而不是静默返回空结果。
"""
import re

from bs4 import BeautifulSoup

from base import BaseCrawler

REVIEW_ID_PATTERN = re.compile(r'/review/(\d+)')
SUBJECT_ID_PATTERN = re.compile(r'/subject/(\d+)')
RATING_CLASS_PATTERN = re.compile(r'(?:allstar|rating)(\d+)')

# 从评论链接的域名判断这篇长评属于哪一类。
SITE_TYPES = {
    'movie.douban.com': 'movie',
    'book.douban.com': 'book',
    'music.douban.com': 'music',
    'www.douban.com': 'game',
}


class ReviewCrawler(BaseCrawler):
    # 长评列表每页 10 篇，与其他分类的 15 不同。
    PAGE_SIZE = 10

    def __init__(
        self,
        session,
        state_store=None,
        request_delay=None,
        baseline=None,
        incremental=False,
        fetch_full_text=False,
    ):
        super().__init__(
            session,
            category_key='reviews',
            state_store=state_store,
            request_delay=request_delay,
            baseline=baseline,
            incremental=incremental,
        )
        self.user_id = None
        self.fetch_full_text = fetch_full_text

    def set_user_id(self, user_id):
        self.user_id = user_id

    def crawl_all_reviews(self):
        """长评没有收藏状态，用单个 collect 伪收藏夹承载全部内容。"""
        url = f"https://www.douban.com/people/{self.user_id}/reviews"
        return {'collect': self.crawl_collection(url, 'collect')}

    def _parse_items(self, response, collection_type=None):
        soup = BeautifulSoup(response.text, 'html.parser')
        blocks = soup.select('div.review-item') or soup.select('div.review')

        items = []
        for block in blocks:
            try:
                review = self._parse_block(block)
                if review:
                    items.append(review)
            except Exception as error:
                print(f"[WARN] 解析长评出错: {error}")
                continue

        if self.fetch_full_text:
            for review in items:
                review['comment'] = self._fetch_full_text(review)

        return items

    def _parse_block(self, block):
        review_link = self._find_review_link(block)
        url = review_link.get('href', '') if review_link else ''

        review_id = ''
        match = REVIEW_ID_PATTERN.search(url)
        if match:
            review_id = match.group(1)

        title = review_link.get_text(strip=True) if review_link else ''
        if not title:
            heading = block.select_one('h2') or block.select_one('.title')
            title = heading.get_text(strip=True) if heading else ''

        subject_tag = (
            block.select_one('a.subject-title')
            or block.select_one('.main-hd a[href*="/subject/"]')
            or block.select_one('a[href*="/subject/"]')
        )
        subject = subject_tag.get_text(strip=True) if subject_tag else ''
        # 列表里的条目名常带一个尾随的 ">"，去掉它。
        subject = subject.rstrip('>').strip()

        subject_id = ''
        if subject_tag:
            match = SUBJECT_ID_PATTERN.search(subject_tag.get('href', '') or '')
            if match:
                subject_id = match.group(1)

        rating = ''
        rating_tag = block.select_one('[class*="allstar"]') or block.select_one(
            '[class*="rating"]'
        )
        if rating_tag:
            for cls in rating_tag.get('class', []):
                match = RATING_CLASS_PATTERN.search(cls)
                if match:
                    value = int(match.group(1))
                    rating = str(value // 10 if value >= 10 else value)
                    break

        date_tag = (
            block.select_one('.main-meta')
            or block.select_one('.main-hd .date')
            or block.select_one('span.date')
        )
        date = date_tag.get_text(strip=True) if date_tag else ''

        body_tag = (
            block.select_one('.short-content')
            or block.select_one('.review-short')
            or block.select_one('.main-bd .content')
        )
        body = self._clean_text(body_tag.get_text(' ', strip=True)) if body_tag else ''
        # 摘要末尾的"(展开)"是页面控件文字，不是正文。
        body = re.sub(r'\(?\s*展开\s*\)?\s*$', '', body).strip()

        if not review_id and not title:
            return None

        return {
            # 用长评自身的 ID 作为条目标识：同一部电影可以写多篇长评，
            # 用被评对象的 ID 会让它们互相覆盖。
            'douban_id': review_id,
            'title': title,
            'subject': subject,
            'subject_id': subject_id,
            'rating': rating,
            'date': date,
            # 正文放进 comment，这样增量比对的指纹、Excel 列和导出逻辑
            # 都能直接复用，不必为长评单开一套。
            'comment': body,
            'url': url,
            'type': 'review',
            'site_type': SITE_TYPES.get(self._host_of(url), ''),
            'collection': '长评',
        }

    def _find_review_link(self, block):
        for selector in (
            '.main-bd h2 a',
            'h2 a[href*="/review/"]',
            'a.title-link',
            'a[href*="/review/"]',
        ):
            link = block.select_one(selector)
            if link is not None:
                return link
        return None

    @staticmethod
    def _host_of(url):
        match = re.match(r'https?://([^/]+)', url or '')
        return match.group(1).lower() if match else ''

    def _fetch_full_text(self, review):
        """打开单篇长评页取完整正文。失败时保留摘要，不让整次备份受影响。"""
        url = review.get('url')
        if not url:
            return review.get('comment', '')

        response = self._make_request(url)
        if response is None:
            print(f"[WARN] 长评正文抓取失败，保留摘要: {review.get('title')}")
            return review.get('comment', '')

        soup = BeautifulSoup(response.text, 'html.parser')
        body = (
            soup.select_one('#link-report .full')
            or soup.select_one('.review-content')
            or soup.select_one('#link-report')
        )
        if body is None:
            print(f"[WARN] 长评正文未解析到，保留摘要: {review.get('title')}")
            return review.get('comment', '')

        return self._clean_text(body.get_text('\n', strip=True))

    def _get_pagination(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        next_link = soup.select_one('span.next a') or soup.select_one('a.next')
        if not next_link:
            return None
        href = next_link.get('href')
        if not href:
            return None
        if href.startswith('http'):
            return href
        return f"https://www.douban.com/people/{self.user_id}/reviews{href}"
