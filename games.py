"""
游戏数据爬取模块
"""
import re
from base import BaseCrawler
from bs4 import BeautifulSoup
from config import DOUBAN_BASE_URL

class GameCrawler(BaseCrawler):
    COLLECTION_MAP = {
        'wish': '想玩',
        'collect': '玩过',
        'do': '在玩'
    }

    def __init__(self, session):
        super().__init__(session)
        self.user_id = None

    def set_user_id(self, user_id):
        self.user_id = user_id

    def crawl_all_games(self):
        # Games use ?action=...
        base = f"https://www.douban.com/people/{self.user_id}/games"
        return {
            'wish': self.crawl(f"{base}?action=wish", 'wish'),
            'collect': self.crawl(f"{base}?action=collect", 'collect'),
            'do': self.crawl(f"{base}?action=do", 'do')
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
                if 'subject' in url:
                    match = re.search(r'subject/(\d+)', url)
                    if match: douban_id = match.group(1)

                img = item.select_one('img')
                cover = img.get('src', '') if img else ''

                rating = ''
                rating_tag = item.select_one('span[class^="allstar"]') or item.select_one('span.rating-star')
                if rating_tag:
                    classes = rating_tag.get('class', [])
                    for cls in classes:
                        if cls.startswith('allstar'):
                            val = cls.replace('allstar', '')
                            if len(val) == 2: rating = str(int(val)//10)
                            break
                    if not rating and rating_tag.get('title'):
                        rating = rating_tag.get('title')

                desc_tag = item.select_one('.desc')
                desc = desc_tag.get_text(strip=True) if desc_tag else ''
                date = ''
                if desc:
                     parts = desc.split('/')
                     if parts: date = parts[0].strip()

                comment = ''
                info_div = item.select_one('.info')
                if info_div:
                     cloned = BeautifulSoup(str(info_div), 'html.parser')
                     for tag in cloned.select('.title, .desc, .rating-info'):
                         tag.decompose()
                     comment = cloned.get_text(strip=True)

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
