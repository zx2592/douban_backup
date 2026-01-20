"""
电影数据爬取模块
"""
import re
from base import BaseCrawler
from base import BaseCrawler
# from config import DOUBAN_BASE_URL # Don't use generic base for movies


class MovieCrawler(BaseCrawler):
    COLLECTION_MAP = {
        'wish': '想看',
        'collect': '看过',
        'do': '在看'
    }

    def __init__(self, session):
        super().__init__(session)
        self.user_id = None

    def set_user_id(self, user_id):
        self.user_id = user_id

    def crawl_wish_movies(self):
        """爬取想看的电影"""
        url = f"https://movie.douban.com/people/{self.user_id}/wish"
        return self.crawl(url, 'wish')

    def crawl_collect_movies(self):
        """爬取已看的电影"""
        url = f"https://movie.douban.com/people/{self.user_id}/collect"
        return self.crawl(url, 'collect')

    def crawl_do_movies(self):
        """爬取在看的电影"""
        url = f"https://movie.douban.com/people/{self.user_id}/do"
        return self.crawl(url, 'do')

    def _parse_items(self, response, collection_type=None):
        """解析电影条目"""
        items = []
        html = response.text

        # Pattern for authenticated page might differ slightly, but let's try to be robust
        # Authenticated view typically has .item .comment
        
        # We'll use BeautifulSoup if regex gets too complex, but sticking to regex for consistency with existing code
        # Actually, switching to BS4 for parsing is cleaner and safer for comment extraction
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        div_items = soup.find_all('div', class_='item')
        
        for item in div_items:
            try:
                # Title
                title = ''
                title_tag = item.select_one('.title a') or item.select_one('.title')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    # Clean title (remove [可播放] etc)
                    title = title.split('/')[0].strip()
                
                # ID & URL
                douban_id = ''
                url = ''
                a_tag = item.find('a', href=True)
                if a_tag:
                    url = a_tag['href']
                    match = re.search(r'subject/(\d+)', url)
                    if match: douban_id = match.group(1)
                
                # Cover
                cover = ''
                img = item.find('img')
                if img: cover = img.get('src', '')
                
                # Rating
                rating = ''
                rating_tag = item.select_one('[class^="rating"][class*="-t"]')
                if rating_tag:
                    # rating5-t
                    match = re.search(r'rating(\d+)-t', rating_tag.get('class', '')[0])
                    if match: rating = match.group(1)
                elif item.select_one('.rating-stars'): 
                     # Some views use this
                     pass

                # Date
                date = ''
                date_tag = item.find('span', class_='date')
                if date_tag: date = date_tag.get_text(strip=True)
                
                # Comment
                comment = ''
                comment_tag = item.find('span', class_='comment')
                if comment_tag: comment = comment_tag.get_text(strip=True)
                
                # Tags
                tags = ''
                tags_tag = item.find('span', class_='tags')
                if tags_tag: tags = tags_tag.get_text(strip=True).replace('标签: ', '')

                item_data = {
                    'douban_id': douban_id,
                    'cover': cover,
                    'title': title,
                    'rating': rating,
                    'date': date,
                    'comment': comment,
                    'tags': tags,
                    'type': 'movie',
                    'collection': self.COLLECTION_MAP.get(collection_type, collection_type)
                }
                items.append(item_data)
            except Exception as e:
                print(f"解析出错: {e}")
                continue

        if not items and not div_items:
            # Fallback to Regex if BS4 finding failed (unlikely if page is valid)
            alt_pattern = r'<li class="ll">.*?href="https://movie\.douban\.com/subject/(\d+)/".*?src="([^"]*)".*?<span class="title">([^<]*)</span>.*?<span class="rating(\d+)-t">'
            alt_matches = re.findall(alt_pattern, html, re.DOTALL)
            for match in alt_matches:
                item = {
                    'douban_id': match[0],
                    'cover': match[1],
                    'title': self._clean_text(match[2]),
                    'rating': match[3],
                    'type': 'movie',
                    'collection': self.COLLECTION_MAP.get(collection_type, collection_type)
                }
                items.append(item)

        return items

    def _get_pagination(self, response):
        """获取下一页链接"""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try common next link patterns
        next_link = soup.select_one('span.next a')
        if not next_link:
             next_link = soup.select_one('a.next')
        
        if next_link:
            href = next_link.get('href')
            if href and not href.startswith('http'):
                return f"https://movie.douban.com{href}"
            return href
            
        return None

    def crawl_all_movies(self):
        """爬取所有电影数据"""
        all_movies = {
            'wish': self.crawl_wish_movies(),
            'collect': self.crawl_collect_movies(),
            'do': self.crawl_do_movies()
        }
        return all_movies
