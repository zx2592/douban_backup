"""
书籍数据爬取模块
"""
import re
from base import BaseCrawler
from base import BaseCrawler
# from config import DOUBAN_BASE_URL


class BookCrawler(BaseCrawler):
    COLLECTION_MAP = {
        'wish': '想读',
        'collect': '已读',
        'reading': '在读'
    }

    def __init__(self, session):
        super().__init__(session)
        self.user_id = None

    def set_user_id(self, user_id):
        self.user_id = user_id

    def crawl_wish_books(self):
        """爬取想读的书籍"""
        url = f"https://book.douban.com/people/{self.user_id}/wish?start=0&type=book"
        return self.crawl(url, 'wish')

    def crawl_collect_books(self):
        """爬取已读的书籍"""
        url = f"https://book.douban.com/people/{self.user_id}/collect?start=0&type=book"
        return self.crawl(url, 'collect')

    def crawl_reading_books(self):
        """爬取在读的书籍"""
        url = f"https://book.douban.com/people/{self.user_id}/reading?start=0&type=book"
        return self.crawl(url, 'reading')

    def _parse_items(self, response, collection_type=None):
        """解析书籍条目"""
        items = []
        html = response.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Try finding items with new selector first
        list_items = soup.find_all('li', class_='subject-item')
        if not list_items:
             list_items = soup.find_all('div', class_='item') # old style/grid
        
        for item in list_items:
            try:
                # Title
                title = ''
                url = ''
                info = item.find('div', class_='info')
                if info:
                    h2 = info.find('h2')
                    if h2 and h2.find('a'):
                        title = h2.find('a').get_text(strip=True)
                        url = h2.find('a')['href']
                    elif item.find('span', class_='title'): # Old style fallback
                         title = item.find('span', class_='title').get_text(strip=True)
                         a = item.find('a', href=True)
                         if a: url = a['href']

                # ID
                douban_id = ''
                if 'subject' in url:
                    match = re.search(r'subject/(\d+)', url)
                    if match: douban_id = match.group(1)
                
                # Cover
                cover = ''
                img = item.find('img')
                if img: cover = img.get('src', '')

                # Author/Pub
                author = ''
                pub = item.find('div', class_='pub')
                if pub:
                    author = pub.get_text(strip=True)
                else:
                    # Fallback
                    author_tag = item.find('span', class_='author')
                    if author_tag: author = author_tag.get_text(strip=True)

                # Rating
                rating = ''
                rating_tag = item.select_one('[class^="rating"][class*="-t"]')
                if rating_tag:
                    match = re.search(r'rating(\d+)-t', rating_tag.get('class', '')[0])
                    if match: rating = match.group(1)

                # Comment
                comment = ''
                comment_tag = item.find('p', class_='comment')
                if comment_tag: comment = comment_tag.get_text(strip=True)
                
                # Date (if available in this view)
                date = ''
                date_tag = item.find('span', class_='date')
                if date_tag: date = date_tag.get_text(strip=True)

                item_data = {
                    'douban_id': douban_id,
                    'cover': cover,
                    'title': title,
                    'author': author,
                    'rating': rating,
                    'comment': comment,
                    'date': date,
                    'type': 'book',
                    'collection': self.COLLECTION_MAP.get(collection_type, collection_type)
                }
                items.append(item_data)
            except Exception as e:
                print(f"解析出错: {e}")
                continue

        return items

    def _get_pagination(self, response):
        """获取下一页链接"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        next_link = soup.select_one('span.next a')
        if not next_link:
             next_link = soup.select_one('a.next')
             
        if next_link:
            href = next_link.get('href')
            if href and not href.startswith('http'):
                return f"https://book.douban.com{href}"
            return href
        return None

    def crawl_all_books(self):
        """爬取所有书籍数据"""
        all_books = {
            'wish': self.crawl_wish_books(),
            'collect': self.crawl_collect_books(),
            'reading': self.crawl_reading_books()
        }
        return all_books
