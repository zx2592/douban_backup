"""
音乐数据爬取模块
"""
import re
from base import BaseCrawler
from bs4 import BeautifulSoup
from config import DOUBAN_BASE_URL

class MusicCrawler(BaseCrawler):
    COLLECTION_MAP = {
        'wish': '想听',
        'collect': '听过',
        'do': '在听'
    }

    def __init__(self, session):
        super().__init__(session)
        self.user_id = None

    def set_user_id(self, user_id):
        self.user_id = user_id

    def crawl_all_music(self):
        return {
            'wish': self.crawl(f"https://music.douban.com/people/{self.user_id}/wish", 'wish'),
            'collect': self.crawl(f"https://music.douban.com/people/{self.user_id}/collect", 'collect'),
            'do': self.crawl(f"https://music.douban.com/people/{self.user_id}/do", 'do')
        }

    def _parse_items(self, response, collection_type=None):
        items = []
        soup = BeautifulSoup(response.text, 'html.parser')
        div_items = soup.select('div.item')
        
        for item in div_items:
            try:
                info = item.select_one('.info')
                if not info: continue
                
                title_tag = info.select_one('a em') or info.select_one('a')
                title = title_tag.get_text(strip=True) if title_tag else ''
                
                url = ''
                a_tag = info.select_one('a')
                if a_tag: url = a_tag.get('href', '')
                
                douban_id = ''
                if 'subject' in url:
                    match = re.search(r'subject/(\d+)', url)
                    if match: douban_id = match.group(1)

                img = item.select_one('img')
                cover = img.get('src', '') if img else ''

                rating_tag = item.select_one('span[class^="rating"]')
                rating = ''
                if rating_tag:
                     match = re.search(r'rating(\d+)', rating_tag.get('class', [''])[0])
                     if match: rating = match.group(1)
                
                intro = ''
                intro_tag = info.select_one('li.intro')
                if intro_tag: intro = intro_tag.get_text(strip=True)
                artist = intro.split('/')[0].strip() if intro else ''

                # Comment
                comment = ''
                lis = info.find_all('li')
                if lis:
                    last_li = lis[-1]
                    if not last_li.get('class'):
                         text = last_li.get_text(strip=True)
                         if not re.match(r'\d{4}-\d{2}-\d{2}', text):
                             comment = text

                items.append({
                    'douban_id': douban_id,
                    'title': title,
                    'artist': artist,
                    'cover': cover,
                    'rating': rating,
                    'info': intro,
                    'comment': comment,
                    'type': 'music',
                    'collection': self.COLLECTION_MAP.get(collection_type, collection_type)
                })
            except Exception as e:
                print(f"Error parsing music: {e}")
                continue
        
        return items

    def _get_pagination(self, response):
        soup = BeautifulSoup(response.text, 'html.parser')
        next_link = soup.select_one('span.next a') # Standard
        if not next_link:
             next_link = soup.select_one('a.next') # Alternative
             
        if next_link:
            href = next_link['href']
            if href and not href.startswith('http'):
                return f"https://music.douban.com{href}"
            return href
        return None
