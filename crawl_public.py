"""
豆瓣数据备份工具 - 针对特定用户
无需登录，爬取公开数据
"""
import json
import os
import re
import time
import sys
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = 'https://www.douban.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

USER_ID = 'lazylazylazy'
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'backup')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def crawl_movies():
    """爬取电影数据"""
    print("\n[电影] 爬取电影数据...")
    all_movies = {'wish': [], 'collect': [], 'do': []}

    collections = [
        ('collect', '已看'),
        ('do', '在看'),
        ('wish', '想看')
    ]

    for coll_type, coll_name in collections:
        print(f"\n  爬取 {coll_name} 的电影...")
        url = f"https://movie.douban.com/people/{USER_ID}/{coll_type}"
        page = 0
        total = 0

        while True:
            page_url = f"{url}?start={page * 15}&sort=time"
            try:
                response = SESSION.get(page_url, timeout=30)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('div', class_='item')

                if not items:
                    break

                for item in items:
                    try:
                        movie = parse_movie_item(item)
                        if movie:
                            all_movies[coll_type].append(movie)
                            total += 1
                    except Exception as e:
                        continue

                print(f"    第{page + 1}页: 获取 {len(items)} 条")

                if len(items) < 15:
                    break

                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"    错误: {e}")
                break

        print(f"  {coll_name}: {total} 部")

    return all_movies


def parse_movie_item(item):
    """解析电影条目"""
    try:
        info = item.find('div', class_='info')
        if not info:
            return None

        title_tag = info.find('a', title=True)
        title = title_tag.get('title', '') if title_tag else ''

        if not title:
            ul = info.find('ul')
            if ul:
                title_tag = ul.find('span', class_='title')
                title = title_tag.get_text(strip=True) if title_tag else ''

        url = title_tag.get('href', '') if title_tag else ''

        subject_id = ''
        if url:
            match = re.search(r'subject/(\d+)', url)
            if match:
                subject_id = match.group(1)

        cover_img = item.find('img')
        cover = cover_img.get('src', '') if cover_img else ''

        rating_tag = item.find('span', class_=lambda x: x and 'rating' in x)
        rating = ''
        if rating_tag:
            rating_class = rating_tag.get('class', [])
            for cls in rating_class:
                if 'rating' in cls and 't' in cls:
                    match = re.search(r'rating(\d+)', cls)
                    if match:
                        rating = match.group(1)
                    break

        date_tag = item.find('span', class_='date')
        date = date_tag.get_text(strip=True) if date_tag else ''

        comment_tag = item.find('span', class_='comment')
        comment = comment_tag.get_text(strip=True) if comment_tag else ''

        return {
            'douban_id': subject_id,
            'title': title,
            'cover': cover,
            'rating': rating,
            'date': date,
            'comment': comment
        }
    except:
        return None


def crawl_books():
    """爬取书籍数据"""
    print("\n[书籍] 爬取书籍数据...")
    all_books = {'wish': [], 'collect': [], 'reading': []}

    collections = [
        ('collect', '已读'),
        ('reading', '在读'),
        ('wish', '想读')
    ]

    for coll_type, coll_name in collections:
        print(f"\n  爬取 {coll_name} 的书籍...")
        url = f"https://book.douban.com/people/{USER_ID}/{coll_type}"
        page = 0
        total = 0

        while True:
            page_url = f"{url}&start={page * 15}"
            try:
                response = SESSION.get(page_url, timeout=30)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.find_all('li', class_='subject-item')

                if not items:
                    items = soup.find_all('div', class_='item') # old style/fallback
                
                if not items:
                    items = soup.find_all('li', class_='item') # another variant

                if not items:
                    break

                for item in items:
                    try:
                        book = parse_book_item(item)
                        if book:
                            all_books[coll_type].append(book)
                            total += 1
                    except:
                        continue

                print(f"    第{page + 1}页: 获取 {len(items)} 条")

                if len(items) < 15:
                    break

                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"    错误: {e}")
                break

        print(f"  {coll_name}: {total} 本")

    return all_books


def parse_book_item(item):
    """解析书籍条目"""
    try:
        # Title
        # Try new style: div.info h2 a
        title = ''
        url = ''
        
        info = item.find('div', class_='info')
        if info:
            h2 = info.find('h2')
            if h2:
                a = h2.find('a')
                if a:
                    title = a.get_text(strip=True)
                    url = a.get('href', '')
        
        # Fallback to old style
        if not title:
            title_tag = item.find('span', class_='title')
            if title_tag:
                 title = title_tag.get_text(strip=True)
                 a = item.find('a', href=True)
                 if a: url = a.get('href', '')

        subject_id = ''
        if 'subject' in url:
            match = re.search(r'subject/(\d+)', url)
            if match:
                subject_id = match.group(1)

        img_tag = item.find('img')
        cover = img_tag.get('src', '') if img_tag else ''

        # Author/Pub
        author = ''
        pub = item.find('div', class_='pub')
        if pub:
            author = pub.get_text(strip=True)
        else:
            author_tag = item.find('span', class_='author')
            if author_tag: author = author_tag.get_text(strip=True)

        # Rating
        rating = ''
        rating_tag = item.find('span', class_=lambda x: x and 'rating' in x)
        if rating_tag:
            rating_class = rating_tag.get('class', [])
            for cls in rating_class:
                if 'rating' in cls and 't' in cls:
                    match = re.search(r'rating(\d+)', cls)
                    if match:
                        rating = match.group(1)
                    break
        
        # Comment
        comment = ''
        comment_tag = item.find('p', class_='comment')
        if comment_tag:
            comment = comment_tag.get_text(strip=True)

        return {
            'douban_id': subject_id,
            'title': title,
            'author': author,
            'cover': cover,
            'rating': rating,
            'comment': comment
        }
    except:
        return None


def crawl_music():
    """爬取音乐数据"""
    print("\n[音乐] 爬取音乐数据...")
    all_music = {'wish': [], 'collect': [], 'do': []}

    collections = [
        ('collect', '听过'),
        ('do', '在听'),
        ('wish', '想听')
    ]

    for coll_type, coll_name in collections:
        print(f"\n  爬取 {coll_name} 的音乐...")
        url = f"https://music.douban.com/people/{USER_ID}/{coll_type}"
        page = 0
        total = 0

        while True:
            page_url = f"{url}?start={page * 15}&sort=time"
            try:
                response = SESSION.get(page_url, timeout=30)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select('div.item')
                
                if not items:
                    break

                for item in items:
                    try:
                        music = parse_music_item(item)
                        if music:
                            all_music[coll_type].append(music)
                            total += 1
                    except:
                        continue

                print(f"    第{page + 1}页: 获取 {len(items)} 条")

                if len(items) < 15:
                    break

                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"    错误: {e}")
                break

        print(f"  {coll_name}: {total} 张")

    return all_music


def parse_music_item(item):
    """解析音乐条目"""
    try:
        info = item.select_one('.info')
        if not info: 
            return None
            
        title_tag = info.select_one('a em') or info.select_one('a')
        title = title_tag.get_text(strip=True) if title_tag else ''
        
        a_tag = info.select_one('a')
        url = a_tag.get('href', '') if a_tag else ''
        subject_id = ''
        if 'subject' in url:
            match = re.search(r'subject/(\d+)', url)
            if match:
                subject_id = match.group(1)

        img_tag = item.select_one('img')
        cover = img_tag.get('src', '') if img_tag else ''

        rating_tag = item.select_one('span[class^="rating"]')
        rating = ''
        if rating_tag:
            rating_class = rating_tag.get('class', [])
            for cls in rating_class:
                if 'rating' in cls and 't' in cls:
                    match = re.search(r'rating(\d+)', cls)
                    if match:
                        rating = match.group(1)
                    break
        
        intro_tag = info.select_one('li.intro')
        intro = intro_tag.get_text(strip=True) if intro_tag else ''
        artist = intro.split('/')[0].strip() if intro else ''

        # Parsing comment logic for Music: often mixed in li
        comment = ''
        # Try finding a list item that is NOT intro, NOT title, NOT rating
        # For music, often the last li if it doesn't have class.
        lis = info.find_all('li')
        if lis:
            last_li = lis[-1]
            if not last_li.get('class'):
                 text = last_li.get_text(strip=True)
                 # Check if it looks like a date/rating line (starts with date usually)
                 # Date format: YYYY-MM-DD
                 if not re.match(r'\d{4}-\d{2}-\d{2}', text):
                     comment = text

        return {
            'douban_id': subject_id,
            'title': title,
            'artist': artist,
            'cover': cover,
            'rating': rating,
            'info': intro,
            'comment': comment
        }
    except:
        return None


def crawl_games():
    """爬取游戏数据"""
    print("\n[游戏] 爬取游戏数据...")
    all_games = {'wish': [], 'collect': [], 'do': []}

    collections = [
        ('collect', '玩过'),
        ('do', '在玩'),
        ('wish', '想玩')
    ]

    for coll_type, coll_name in collections:
        print(f"\n  爬取 {coll_name} 的游戏...")
        url = f"https://www.douban.com/people/{USER_ID}/games" 
        page = 0
        total = 0

        while True:
            page_url = f"{url}?action={coll_type}&start={page * 15}"
            try:
                response = SESSION.get(page_url, timeout=30)
                if response.status_code != 200:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                items = soup.select('div.common-item')
                
                if not items:
                    break

                for item in items:
                    try:
                        game = parse_game_item(item)
                        if game:
                            all_games[coll_type].append(game)
                            total += 1
                    except:
                        continue

                print(f"    第{page + 1}页: 获取 {len(items)} 条")

                if len(items) < 15:
                    break

                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"    错误: {e}")
                break

        print(f"  {coll_name}: {total} 个")

    return all_games


def parse_game_item(item):
    """解析游戏条目"""
    try:
        title_tag = item.select_one('.title a')
        title = title_tag.get_text(strip=True) if title_tag else ''
        
        url = title_tag.get('href', '') if title_tag else ''
        subject_id = ''
        if 'subject' in url:
            match = re.search(r'subject/(\d+)', url)
            if match:
                subject_id = match.group(1)

        img_tag = item.select_one('img')
        cover = img_tag.get('src', '') if img_tag else ''

        rating = ''
        rating_tag = item.select_one('span[class^="allstar"]') or item.select_one('span.rating-star')
        if rating_tag:
            classes = rating_tag.get('class', [])
            for cls in classes:
                if cls.startswith('allstar'):
                    rating = cls.replace('allstar', '')
                    if len(rating) == 2:
                        rating = str(int(rating) // 10)
                    break
            
            if not rating and rating_tag.get('title'):
                rating = rating_tag.get('title')

        desc_tag = item.select_one('.desc')
        desc = desc_tag.get_text(strip=True) if desc_tag else ''
        
        date = ''
        if desc:
             parts = desc.split('/')
             if parts:
                 date = parts[0].strip()

        # Comment for Games: text in .info div
        comment = ''
        try:
             # This is tricky as structure varies. Attempt provided strategy.
             info_div = item.select_one('.info')
             if info_div:
                 # Get text that is NOT inside desc or title
                 cloned_info = BeautifulSoup(str(info_div), 'html.parser')
                 for tag in cloned_info.select('.title, .desc, .rating-info'):
                     tag.decompose()
                 comment = cloned_info.get_text(strip=True)
        except:
            pass

        return {
            'douban_id': subject_id,
            'title': title,
            'cover': cover,
            'rating': rating,
            'date': date,
            'info': desc,
            'comment': comment
        }
    except:
        return None


def save_json(data, filename):
    """保存JSON文件"""
    filepath = os.path.join(OUTPUT_DIR, f"{filename}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 已保存: {filepath}")
    return filepath


def save_excel(data, filename):
    """保存Excel文件"""
    filepath = os.path.join(OUTPUT_DIR, f"{filename}.xlsx")
    wb = Workbook()
    ws = wb.active

    ws.append(['类型', '收藏状态', '标题', '豆瓣ID', '评分', '评语', '作者/音乐人/日期', '日期/封面/详情'])

    for category, collections in data.items():
        for coll, items in collections.items():
            for item in items:
                # Normalize fields for different types
                field1 = item.get('author') or item.get('artist') or item.get('year') or item.get('date') or ''
                field2 = item.get('date') or item.get('cover') or item.get('info') or ''
                
                row = [
                    category,
                    coll,
                    item.get('title', ''),
                    item.get('douban_id', ''),
                    item.get('rating', ''),
                    item.get('comment', ''),
                    field1,
                    field2
                ]
                ws.append(row)

    wb.save(filepath)
    print(f"✓ 已保存: {filepath}")
    return filepath


def main():
    print("=" * 50)
    print("[豆瓣数据备份工具]")
    print("=" * 50)
    print(f"\n用户: {USER_ID}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    all_data = {}

    try:
        all_data['movies'] = crawl_movies()
        save_json(all_data['movies'], f"movies_{timestamp}")

        all_data['books'] = crawl_books()
        save_json(all_data['books'], f"books_{timestamp}")

        all_data['music'] = crawl_music()
        save_json(all_data['music'], f"music_{timestamp}")

        all_data['games'] = crawl_games()
        save_json(all_data['games'], f"games_{timestamp}")

        save_json(all_data, f"douban_backup_{timestamp}")
        save_excel(all_data, f"douban_backup_{timestamp}")

        print("\n" + "=" * 50)
        print("[备份统计]")
        print("=" * 50)
        movies_total = sum(len(v) for v in all_data['movies'].values())
        books_total = sum(len(v) for v in all_data['books'].values())
        music_total = sum(len(v) for v in all_data.get('music', {}).values())
        games_total = sum(len(v) for v in all_data.get('games', {}).values())
        print(f"  电影: {movies_total} 部")
        print(f"  书籍: {books_total} 本")
        print(f"  音乐: {music_total} 张")
        print(f"  游戏: {games_total} 个")
        print(f"\n文件保存在: {OUTPUT_DIR}")

    except KeyboardInterrupt:
        print("\n\n用户中断，保存已获取的数据...")
        if all_data:
            save_json(all_data, f"douban_backup_interrupted_{timestamp}")
            save_excel(all_data, f"douban_backup_interrupted_{timestamp}")


if __name__ == '__main__':
    main()
