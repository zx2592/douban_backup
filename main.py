"""
豆瓣数据备份工具主程序
"""
import argparse
import getpass
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import DoubanAuth
from backup_metadata import build_metadata
from backup_state import BackupState
from books import BookCrawler
from config import BACKUP_ITEMS, DATA_DIR, REQUEST_TIMEOUT
from crawl_public import run_public_backup
from diagnostics import classify_response
from games import GameCrawler
from movies import MovieCrawler
from music import MusicCrawler
from storage import DataStorage


VALID_CATEGORIES = ["movies", "books", "music", "games"]
CATEGORY_LABELS = {
    "movies": ("电影", "部"),
    "books": ("书籍", "本"),
    "music": ("音乐", "张"),
    "games": ("游戏", "个"),
}


def parse_category_list(raw_value):
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def non_negative_delay(raw_value):
    try:
        delay = float(raw_value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("间隔时间必须是数字。") from error
    if delay < 0:
        raise argparse.ArgumentTypeError("间隔时间不能小于 0。")
    return delay


def resolve_selected_items(only=None, skip=None):
    if only:
        selected = parse_category_list(only)
    else:
        selected = [name for name, enabled in BACKUP_ITEMS.items() if enabled]

    invalid = [item for item in selected if item not in VALID_CATEGORIES]
    if invalid:
        raise ValueError(f"不支持的分类: {', '.join(invalid)}")

    skip_items = parse_category_list(skip)
    invalid_skip = [item for item in skip_items if item not in VALID_CATEGORIES]
    if invalid_skip:
        raise ValueError(f"不支持的跳过分类: {', '.join(invalid_skip)}")

    selected = [item for item in selected if item not in skip_items]
    if not selected:
        raise ValueError("至少需要保留一个备份分类。")

    return selected


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="豆瓣数据备份工具")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["verify", "list", *VALID_CATEGORIES],
        help="verify 校验登录和页面可访问性；list 查看备份；或指定单个分类备份",
    )
    parser.add_argument("--only", help="仅备份指定分类，逗号分隔，例如 movies,books")
    parser.add_argument("--skip", help="跳过指定分类，逗号分隔，例如 music,games")
    parser.add_argument("--public", metavar="USER_ID", help="使用公开页面模式备份指定用户")
    parser.add_argument("--output", help="导出目录，默认使用 data/backup")
    parser.add_argument(
        "--delay",
        type=non_negative_delay,
        metavar="SECONDS",
        help="每次请求之间等待的秒数；默认登录备份为 2 秒，公开备份为 1 秒",
    )
    parser.add_argument("--no-resume", action="store_true", help="禁用断点续传")
    return parser.parse_args(argv)


class DoubanBackup:
    def __init__(
        self,
        selected_items=None,
        output_dir=None,
        checkpoint_enabled=True,
        request_delay=None,
    ):
        self.auth = DoubanAuth()
        self.selected_items = list(selected_items or VALID_CATEGORIES)
        self.output_dir = output_dir
        self.storage = DataStorage(backup_dir=output_dir)
        self.checkpoint_enabled = checkpoint_enabled
        self.request_delay = request_delay
        self.state_store = None
        self.session = None
        self.user_id = None
        self.user_name = None
        self.backup_incomplete = False

    def _build_metadata(self, backup_mode, selected_items=None):
        return build_metadata(
            backup_mode=backup_mode,
            selected_categories=selected_items or self.selected_items,
            user_id=self.user_id,
            output_dir=self.storage.backup_dir,
        )

    def _prepare_storage(self, backup_mode, selected_items=None):
        self.storage.set_metadata(self._build_metadata(backup_mode, selected_items))

    def run(self):
        """主运行函数"""
        print("=" * 50)
        print("豆瓣数据备份工具")
        print("=" * 50)

        if not self._login():
            return False

        self._prepare_storage("authenticated")
        try:
            print("\n开始备份数据...")
            all_data = self._backup_all()

            print("\n保存数据...")
            self.storage.save_all_json(all_data)
            self.storage.save_all_excel(all_data)

            if self.backup_incomplete or (
                self.state_store and self.state_store.has_incomplete_collections()
            ):
                print("\n[WARN] 本次备份未完整结束，已保存部分数据和断点。")
                self._print_summary(all_data)
                return False

            if self.state_store:
                self.state_store.clear()

            print("\n备份完成!")
            self._print_summary(all_data)
            return True
        except KeyboardInterrupt:
            print("\n[WARN] 已中断，断点状态已保存，下次运行会从上次进度继续。")
            return False

    def verify(self):
        """验证 Cookie、用户信息和分类页面可访问性。"""
        print("=" * 50)
        print("豆瓣备份环境校验")
        print("=" * 50)

        report = {
            "ok": False,
            "login_ok": False,
            "user": None,
            "checks": [],
        }

        if not self.auth.login_with_cookies():
            report["error_code"] = "login_expired"
            report["message"] = "Cookie 无效或已过期，请重新导入。"
            print(f"[ERROR] {report['message']}")
            return report

        self.session = self.auth.get_session()
        user_info = self._load_user_info()
        if not self.user_id:
            report["error_code"] = "user_id_missing"
            report["message"] = "登录成功，但未能识别当前用户。"
            print(f"[ERROR] {report['message']}")
            return report

        report["login_ok"] = True
        report["user"] = user_info or {"id": self.user_id, "name": self.user_name}
        print(f"[OK] 当前用户: {self.user_name or self.user_id} ({self.user_id})")

        for category, url in self._build_category_urls().items():
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            except Exception as exc:
                report["checks"].append(
                    {
                        "category": category,
                        "status": "error",
                        "code": "request_failed",
                        "message": f"请求失败: {exc}",
                        "url": url,
                    }
                )
                print(f"[ERROR] {CATEGORY_LABELS[category][0]}: 请求失败: {exc}")
                continue

            status, code, message = classify_response(response)
            report["checks"].append(
                {
                    "category": category,
                    "status": status,
                    "code": code,
                    "message": message,
                    "url": url,
                }
            )
            prefix = "[OK]" if status == "ok" else "[WARN]"
            print(f"{prefix} {CATEGORY_LABELS[category][0]}: {message}")

        report["ok"] = report["login_ok"] and all(
            check["status"] == "ok" for check in report["checks"]
        )
        return report

    def _build_category_urls(self):
        urls = {
            "movies": f"https://movie.douban.com/people/{self.user_id}/collect",
            "books": f"https://book.douban.com/people/{self.user_id}/collect?start=0&type=book",
            "music": f"https://music.douban.com/people/{self.user_id}/collect",
            "games": f"https://www.douban.com/people/{self.user_id}/games?action=collect",
        }
        return {category: urls[category] for category in self.selected_items}

    def _login(self):
        """登录豆瓣"""
        print("\n[1/2] 登录豆瓣账号")

        if self.auth.login_with_cookies():
            return self._finalize_login()

        email = input("请输入豆瓣邮箱: ").strip()
        password = getpass.getpass("请输入密码（输入时不显示）: ")

        if self.auth.login(email, password):
            return self._finalize_login()

        print("登录失败!")
        return False

    def _finalize_login(self):
        """完成认证后的会话和用户信息校验。"""
        self.session = self.auth.get_session()
        self._load_user_info()
        if self.user_id:
            if self.checkpoint_enabled:
                self.state_store = BackupState(
                    self.storage.backup_dir,
                    user_id=self.user_id,
                )
            return True

        self.session = None
        print("[WARN] 登录成功，但未能识别当前用户 ID。请重新导入 Cookie 后再试。")
        return False

    def _load_user_info(self):
        """加载用户信息"""
        user_info_file = os.path.join(DATA_DIR, "user_info.json")
        if not os.path.exists(user_info_file):
            return None

        with open(user_info_file, "r", encoding="utf-8") as f:
            user_info = json.load(f)

        self.user_id = user_info.get("id")
        self.user_name = user_info.get("name")
        print(f"欢迎, {self.user_name or self.user_id or ''}")
        return user_info

    def _backup_all(self):
        """备份所有数据"""
        all_data = {}

        if "movies" in self.selected_items:
            print("\n[电影] 备份电影...")
            movie_crawler = MovieCrawler(
                self.session,
                state_store=self.state_store,
                request_delay=self.request_delay,
            )
            movie_crawler.set_user_id(self.user_id)
            all_data["movies"] = movie_crawler.crawl_all_movies()
            self.backup_incomplete |= movie_crawler.incomplete

        if "books" in self.selected_items:
            print("\n[书籍] 备份书籍...")
            book_crawler = BookCrawler(
                self.session,
                state_store=self.state_store,
                request_delay=self.request_delay,
            )
            book_crawler.set_user_id(self.user_id)
            all_data["books"] = book_crawler.crawl_all_books()
            self.backup_incomplete |= book_crawler.incomplete

        if "music" in self.selected_items:
            print("\n[音乐] 备份音乐...")
            music_crawler = MusicCrawler(
                self.session,
                state_store=self.state_store,
                request_delay=self.request_delay,
            )
            music_crawler.set_user_id(self.user_id)
            all_data["music"] = music_crawler.crawl_all_music()
            self.backup_incomplete |= music_crawler.incomplete

        if "games" in self.selected_items:
            print("\n[游戏] 备份游戏...")
            game_crawler = GameCrawler(
                self.session,
                state_store=self.state_store,
                request_delay=self.request_delay,
            )
            game_crawler.set_user_id(self.user_id)
            all_data["games"] = game_crawler.crawl_all_games()
            self.backup_incomplete |= game_crawler.incomplete

        return all_data

    def _print_summary(self, data):
        """打印备份摘要"""
        print("\n备份统计:")
        for category in self.selected_items:
            if category not in data:
                continue
            total = sum(len(v) for v in data[category].values())
            label, unit = CATEGORY_LABELS[category]
            print(f"  {label}: {total} {unit}")

        print(f"\n文件已保存到 {self.storage.backup_dir}")

    def backup_category(self, category):
        """备份一个指定分类。"""
        if not self._login():
            return False

        crawler_class, crawl_method = {
            "movies": (MovieCrawler, "crawl_all_movies"),
            "books": (BookCrawler, "crawl_all_books"),
            "music": (MusicCrawler, "crawl_all_music"),
            "games": (GameCrawler, "crawl_all_games"),
        }[category]

        self._prepare_storage("authenticated", [category])
        crawler = crawler_class(
            self.session,
            state_store=self.state_store,
            request_delay=self.request_delay,
        )
        crawler.set_user_id(self.user_id)
        category_data = getattr(crawler, crawl_method)()
        data = {category: category_data}

        self.storage.save_json(category_data, category)
        self.storage.save_excel(data, category)
        if crawler.incomplete or (
            self.state_store and self.state_store.has_incomplete_collections()
        ):
            print("\n[WARN] 本次备份未完整结束，已保存部分数据和断点。")
            self._print_summary(data)
            return False
        if self.state_store:
            self.state_store.clear()
        self._print_summary(data)
        return True

    def list_backups(self):
        """列出已有备份"""
        backups = self.storage.get_backup_list()
        print("\n已有备份:")
        for backup in backups:
            print(
                f"  {backup['modified']} - {backup['name']} ({backup['size']/1024:.1f} KB)"
            )
        return backups


def main(argv=None):
    args = parse_args(argv)
    selected_items = resolve_selected_items(args.only, args.skip)

    if args.public:
        return run_public_backup(
            args.public,
            categories=selected_items,
            output_dir=args.output,
            request_delay=args.delay,
        )

    backup = DoubanBackup(
        selected_items=selected_items,
        output_dir=args.output,
        checkpoint_enabled=not args.no_resume,
        request_delay=args.delay,
    )

    if args.command == "verify":
        return backup.verify()
    if args.command == "list":
        return backup.list_backups()
    if args.command in VALID_CATEGORIES:
        return backup.backup_category(args.command)

    return backup.run()


if __name__ == "__main__":
    main()
