"""豆瓣公开数据备份 —— 无需登录，抓取指定用户公开主页上的收藏。

这里不再自带一套抓取和导出逻辑，而是复用 base.py 的抓取栈（失败重试、
响应诊断、断点续传、增量比对）和 storage.py 的导出逻辑。公开模式与登录
模式的真正差别只有两点：这里的 session 不带 Cookie，以及默认请求间隔
更短（公开页压力小一些）。

之所以合并，是因为豆瓣改一次页面结构原本要改两处解析代码，而公开模式
那份既没有重试也没有断点，分页还只靠"不足一页即结束"的启发式判断。
"""
import argparse
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backup_metadata import build_metadata
from backup_state import BackupState
from books import BookCrawler
from cli import exit_code
from config import HEADERS
from covers import CoverDownloader
from games import GameCrawler
from incremental import Baseline
from movies import MovieCrawler
from reviews import ReviewCrawler
from music import MusicCrawler
from storage import DataStorage

DEFAULT_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), 'data', 'backup'
)
DEFAULT_CATEGORIES = ['movies', 'books', 'music', 'games', 'reviews']

# 公开页不需要登录态，抓取压力较小，默认间隔比登录备份（2 秒）短一些。
DEFAULT_REQUEST_DELAY = 1

# 分类 -> (爬虫类, 入口方法, 中文名, 量词)
CATEGORY_CRAWLERS = {
    'movies': (MovieCrawler, 'crawl_all_movies', '电影', '部'),
    'books': (BookCrawler, 'crawl_all_books', '书籍', '本'),
    'music': (MusicCrawler, 'crawl_all_music', '音乐', '张'),
    'games': (GameCrawler, 'crawl_all_games', '游戏', '个'),
    'reviews': (ReviewCrawler, 'crawl_all_reviews', '长评', '篇'),
}


def build_public_session():
    """公开模式用的会话：只带浏览器 UA，不带任何登录 Cookie。"""
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def state_key(user_id):
    """公开模式的断点和基线与登录模式分开存放。

    同一个账号既可能备份自己的登录数据，也可能备份自己的公开主页，两者
    抓到的条目并不相同（公开页看不到设为私密的条目）。共用一份基线会让
    增量比对得出错误结论，所以这里加前缀把两者隔离开。
    """
    return f"public:{user_id}"


def run_public_backup(
    user_id,
    categories=None,
    output_dir=None,
    request_delay=None,
    checkpoint_enabled=True,
    incremental=False,
    download_covers=False,
    full_reviews=False,
):
    categories = list(categories or DEFAULT_CATEGORIES)
    if request_delay is None:
        request_delay = DEFAULT_REQUEST_DELAY

    storage = DataStorage(backup_dir=output_dir or DEFAULT_OUTPUT_DIR)
    metadata = build_metadata(
        backup_mode='public',
        selected_categories=categories,
        user_id=user_id,
        output_dir=storage.backup_dir,
    )
    storage.set_metadata(metadata)

    session = build_public_session()
    key = state_key(user_id)
    state_store = (
        BackupState(storage.backup_dir, user_id=key) if checkpoint_enabled else None
    )
    baseline = Baseline(storage.backup_dir, user_id=key)

    print("=" * 50)
    print("[豆瓣数据备份工具 - 公开数据]")
    print("=" * 50)
    print(f"\n用户: {user_id}")
    print(f"时间: {metadata['generated_at']}")
    if incremental and baseline.is_empty():
        print("[增量] 尚无基线数据，本次将完整备份并建立基线。")

    all_data = {}
    incomplete = False
    timestamp = storage.new_timestamp()

    try:
        for category in categories:
            crawler_class, crawl_method, label, _unit = CATEGORY_CRAWLERS[category]
            print(f"\n[{label}] 爬取{label}数据...")
            extra = {'fetch_full_text': full_reviews} if category == 'reviews' else {}
            crawler = crawler_class(
                session,
                state_store=state_store,
                request_delay=request_delay,
                baseline=baseline,
                incremental=incremental,
                **extra,
            )
            crawler.set_user_id(user_id)
            all_data[category] = getattr(crawler, crawl_method)()
            incomplete |= crawler.incomplete
    except KeyboardInterrupt:
        print("\n\n用户中断，保存已获取的数据...")
        if all_data:
            storage.save_all_json(all_data, timestamp=f"interrupted_{timestamp}")
            storage.save_all_excel(all_data, timestamp=f"interrupted_{timestamp}")
        return {"ok": False, "data": all_data}

    if download_covers:
        print("\n下载封面...")
        CoverDownloader(session, storage.backup_dir).download_all(all_data)

    storage.save_all_json(all_data, timestamp=timestamp)
    storage.save_all_excel(all_data, timestamp=timestamp)

    incomplete = incomplete or (
        state_store is not None and state_store.has_incomplete_collections()
    )
    if incomplete:
        print("\n[WARN] 本次备份未完整结束，已保存部分数据和断点。")
    else:
        if state_store:
            state_store.clear()
        # 只有完整跑完的备份才配更新基线，否则下次增量会在残缺数据的
        # 边界停下，中间那段再也抓不回来。
        for category, collections in all_data.items():
            for collection, items in collections.items():
                baseline.update(category, collection, items)
        baseline.save()

    print("\n" + "=" * 50)
    print("[备份统计]")
    print("=" * 50)
    for category in categories:
        total = sum(len(v) for v in all_data.get(category, {}).values())
        _, _, label, unit = CATEGORY_CRAWLERS[category]
        print(f"  {label}: {total} {unit}")
    print(f"\n文件保存在: {storage.backup_dir}")
    return {"ok": not incomplete, "data": all_data}


def non_negative_delay(raw_value):
    try:
        delay = float(raw_value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("间隔时间必须是数字。") from error
    if delay < 0:
        raise argparse.ArgumentTypeError("间隔时间不能小于 0。")
    return delay


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="豆瓣公开数据备份工具")
    parser.add_argument("user_id", nargs="?", help="豆瓣用户 ID")
    parser.add_argument(
        "--delay",
        type=non_negative_delay,
        metavar="SECONDS",
        help="每次请求之间等待的秒数，默认 1 秒",
    )
    parser.add_argument("--output", help="导出目录，默认使用 data/backup")
    parser.add_argument("--no-resume", action="store_true", help="禁用断点续传")
    parser.add_argument(
        "--full-reviews",
        action="store_true",
        help="抓取长评完整正文（默认只保存摘要）；每篇长评需要额外一次请求",
    )
    parser.add_argument(
        "--download-covers",
        action="store_true",
        help="把封面图片下载到导出目录的 covers/ 子目录",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="增量备份：只抓取上次备份之后新增或改动的条目（不会同步已删除的收藏）",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    user_id = args.user_id

    if not user_id:
        user_id = input("请输入豆瓣用户ID: ").strip()
        if not user_id:
            print("用户ID不能为空!")
            print("用法: python crawl_public.py <用户ID> [--delay 秒数] [--incremental]")
            return None

    return run_public_backup(
        user_id,
        output_dir=args.output,
        request_delay=args.delay,
        checkpoint_enabled=not args.no_resume,
        incremental=args.incremental,
        download_covers=args.download_covers,
        full_reviews=args.full_reviews,
    )


if __name__ == '__main__':
    sys.exit(exit_code(main()))
