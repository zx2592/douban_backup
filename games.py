"""
游戏数据爬取模块
"""
import re
from base import BaseCrawler
from bs4 import BeautifulSoup
from comments import extract_comment

# 豆瓣评分的中文说法与星级的对应关系。游戏条目的评分有时只以 title
# 属性给出（如 title="力荐"），必须换算成数字才能和其他分类一致。
RATING_TITLES = {
    '力荐': '5',
    '推荐': '4',
    '还行': '3',
    '较差': '2',
    '很差': '1',
}


class GameCrawler(BaseCrawler):
    COLLECTION_MAP = {
        'wish': '想玩',
        'collect': '玩过',
        'do': '在玩'
    }

    def __init__(
        self,
        session,
        state_store=None,
        request_delay=None,
        baseline=None,
        incremental=False,
    ):
        super().__init__(
            session,
            category_key='games',
            state_store=state_store,
            request_delay=request_delay,
            baseline=baseline,
            incremental=incremental,
        )
        self.user_id = None

    def set_user_id(self, user_id):
        self.user_id = user_id

    def crawl_all_games(self):
        # Games use ?action=...
        base = f"https://www.douban.com/people/{self.user_id}/games"
        return {
            'wish': self.crawl_collection(f"{base}?action=wish", 'wish'),
            'collect': self.crawl_collection(f"{base}?action=collect", 'collect'),
            'do': self.crawl_collection(f"{base}?action=do", 'do')
        }

    def _parse_items(self, response, collection_type=None):
        items = []
        soup = BeautifulSoup(response.text, 'html.parser')
        div_items = soup.select('div.common-item')
        
        for item in div_items:
            try:
                title_tag = item.select_one('.title a')
                title = title_tag.get_text(strip=True) if title_tag else ''
                
                url = title_tag.get('href', '') if title_tag else ''
                douban_id = ''
                match = re.search(r'(?:subject|game)/(\d+)', url)
                if match:
                    douban_id = match.group(1)

                img = item.select_one('img')
                cover = img.get('src', '') if img else ''

                rating = ''
                rating_tag = item.select_one('span[class^="allstar"]') or item.select_one('span.rating-star')
                if rating_tag:
                    for cls in rating_tag.get('class', []):
                        # allstar50 表示 5 星、allstar40 表示 4 星。用正则取数字
                        # 而不是切字符串，遇到 allstar-hidden 这类无数字的 class
                        # 时才不会抛异常把整个条目丢掉。
                        match = re.search(r'allstar(\d+)', cls)
                        if match:
                            value = int(match.group(1))
                            rating = str(value // 10 if value >= 10 else value)
                            break
                    if not rating:
                        # title 属性是"力荐/推荐/还行"这类中文，必须换算成
                        # 数字。原样写入的话，JSON 里是中文，导出 Excel 时
                        # 又因为不是数字而被静默丢弃，两边都不对。
                        # 注意别用 title 这个变量名接，那是条目标题。
                        rating_title = (rating_tag.get('title') or '').strip()
                        rating = RATING_TITLES.get(rating_title, '')

                desc_tag = item.select_one('.desc')
                desc = desc_tag.get_text(strip=True) if desc_tag else ''
                date = ''
                if desc:
                     parts = desc.split('/')
                     if parts: date = parts[0].strip()

                # 游戏的评语是条目末尾一个没有 class 的 p，同样不能只认
                # .comment；简介和评语挨着，要把简介排除掉。
                comment = extract_comment(item, exclude_texts=(desc,))

                items.append({
                    'douban_id': douban_id,
                    'title': title,
                    'cover': cover,
                    'rating': rating,
                    'date': date,
                    'info': desc,
                    'comment': comment,
                    'type': 'game',
                    'collection': self.COLLECTION_MAP.get(collection_type, collection_type)
                })
            except Exception as e:
                print(f"Error parsing game: {e}")
                continue
        
        return items

    def _get_pagination(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        next_link = soup.select_one('span.next a')
        if next_link:
            href = next_link['href']
            if not href.startswith('http'):
                # Games pagination is relative like ?action=wish&start=15
                return f"https://www.douban.com/people/{self.user_id}/games{href}"
            return href
        return None
