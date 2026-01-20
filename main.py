"""
豆瓣数据备份工具主程序
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import DoubanAuth
from movies import MovieCrawler
from books import BookCrawler
from music import MusicCrawler
from games import GameCrawler
from storage import DataStorage
from config import BACKUP_ITEMS


class DoubanBackup:
    def __init__(self):
        self.auth = DoubanAuth()
        self.storage = DataStorage()
        self.session = None
        self.user_id = None

    def run(self):
        """主运行函数"""
        print("=" * 50)
        print("豆瓣数据备份工具")
        print("=" * 50)

        if not self._login():
            return

        print("\n开始备份数据...")
        all_data = self._backup_all()

        print("\n保存数据...")
        self.storage.save_all_json(all_data)
        self.storage.save_all_excel(all_data)

        print("\n备份完成!")
        self._print_summary(all_data)

    def _login(self):
        """登录豆瓣"""
        print("\n[1/2] 登录豆瓣账号")

        if self.auth.login_with_cookies():
            self.session = self.auth.get_session()
            self._load_user_info()
            return True

        email = input("请输入豆瓣邮箱: ").strip()
        password = input("请输入密码: ")

        if self.auth.login(email, password):
            self.session = self.auth.get_session()
            self._load_user_info()
            return True

        print("登录失败!")
        return False

    def _load_user_info(self):
        """加载用户信息"""
        user_info_file = os.path.join('data', 'user_info.json')
        if os.path.exists(user_info_file):
            with open(user_info_file, 'r', encoding='utf-8') as f:
                import json
                user_info = json.load(f)
                self.user_id = user_info.get('id')
                print(f"欢迎, {user_info.get('name', '')}")

    def _backup_all(self):
        """备份所有数据"""
        all_data = {}

        if BACKUP_ITEMS.get('movies'):
            print("\n[2/3] 备份电影...")
            movie_crawler = MovieCrawler(self.session)
            movie_crawler.set_user_id(self.user_id)
            all_data['movies'] = movie_crawler.crawl_all_movies()

        if BACKUP_ITEMS.get('books'):
            print("\n[3/4] 备份书籍...")
            book_crawler = BookCrawler(self.session)
            book_crawler.set_user_id(self.user_id)
            all_data['books'] = book_crawler.crawl_all_books()

        if BACKUP_ITEMS.get('music'):
            print("\n[音乐] 备份音乐...")
            music_crawler = MusicCrawler(self.session)
            music_crawler.set_user_id(self.user_id)
            all_data['music'] = music_crawler.crawl_all_music()

        if BACKUP_ITEMS.get('games'):
            print("\n[游戏] 备份游戏...")
            game_crawler = GameCrawler(self.session)
            game_crawler.set_user_id(self.user_id)
            all_data['games'] = game_crawler.crawl_all_games()

        return all_data

    def _print_summary(self, data):
        """打印备份摘要"""
        print("\n备份统计:")
        if 'movies' in data:
            total = sum(len(v) for v in data['movies'].values())
            print(f"  电影: {total} 部")

        if 'books' in data:
            total = sum(len(v) for v in data['books'].values())
            print(f"  书籍: {total} 本")

        if 'music' in data:
            total = sum(len(v) for v in data['music'].values())
            print(f"  音乐: {total} 张")

        if 'games' in data:
            total = sum(len(v) for v in data['games'].values())
            print(f"  游戏: {total} 个")

        print("\n文件已保存到 data/backup/ 目录")

    def backup_movies_only(self):
        """只备份电影"""
        if not self._login():
            return

        movie_crawler = MovieCrawler(self.session)
        movie_crawler.set_user_id(self.user_id)
        movies = movie_crawler.crawl_all_movies()

        self.storage.save_movies_json(movies)
        self.storage.save_excel({'movies': movies}, 'movies')

    def backup_movies_with_creds(self, email=None, password=None):
        """使用指定账号密码备份电影"""
        if email and password:
            if self.auth.login(email, password):
                self.session = self.auth.get_session()
                self._load_user_info()
            else:
                print("登录失败!")
                return
        elif not self._login():
            return

        movie_crawler = MovieCrawler(self.session)
        movie_crawler.set_user_id(self.user_id)
        movies = movie_crawler.crawl_all_movies()

        self.storage.save_movies_json(movies)
        self.storage.save_excel({'movies': movies}, 'movies')
        self._print_summary({'movies': movies})

    def backup_books_only(self):
        """只备份书籍"""
        if not self._login():
            return

        book_crawler = BookCrawler(self.session)
        book_crawler.set_user_id(self.user_id)
        books = book_crawler.crawl_all_books()

        self.storage.save_books_json(books)
        self.storage.save_excel({'books': books}, 'books')

    def backup_books_with_creds(self, email=None, password=None):
        """使用指定账号密码备份书籍"""
        if email and password:
            if self.auth.login(email, password):
                self.session = self.auth.get_session()
                self._load_user_info()
            else:
                print("登录失败!")
                return
        elif not self._login():
            return

        book_crawler = BookCrawler(self.session)
        book_crawler.set_user_id(self.user_id)
        books = book_crawler.crawl_all_books()

        self.storage.save_books_json(books)
        self.storage.save_excel({'books': books}, 'books')
        self._print_summary({'books': books})

    def list_backups(self):
        """列出已有备份"""
        backups = self.storage.get_backup_list()
        print("\n已有备份:")
        for b in backups:
            print(f"  {b['modified']} - {b['name']} ({b['size']/1024:.1f} KB)")


def main():
    backup = DoubanBackup()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'movies':
            email = sys.argv[2] if len(sys.argv) > 2 else None
            password = sys.argv[3] if len(sys.argv) > 3 else None
            backup.backup_movies_with_creds(email, password)
        elif command == 'books':
            email = sys.argv[2] if len(sys.argv) > 2 else None
            password = sys.argv[3] if len(sys.argv) > 3 else None
            backup.backup_books_with_creds(email, password)
        elif command == 'list':
            backup.list_backups()
        else:
            print("用法: python main.py [movies|books|list] [email] [password]")
    else:
        backup.run()


if __name__ == '__main__':
    main()
