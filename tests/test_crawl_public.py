import unittest
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup

import crawl_public


class DummyResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


class CrawlPublicTests(unittest.TestCase):
    FIXTURE_DIR = Path(__file__).parent / "fixtures"

    def fixture_item(self, filename, selector):
        html = (self.FIXTURE_DIR / filename).read_text(encoding="utf-8")
        return BeautifulSoup(html, "html.parser").select_one(selector)

    def test_parse_book_item_reads_comment_from_any_comment_element(self):
        item = self.fixture_item("book_collection_item.html", ".subject-item")

        self.assertEqual(crawl_public.parse_book_item(item)["comment"], "标签不是 p 也应抓到")

    def test_parse_music_item_keeps_comment_next_to_date(self):
        item = self.fixture_item("music_collection_item.html", ".item")

        self.assertEqual(crawl_public.parse_music_item(item)["comment"], "日期同节点的音乐短评")

    def test_parse_game_item_reads_only_comment(self):
        item = self.fixture_item("game_collection_item.html", ".common-item")

        parsed = crawl_public.parse_game_item(item)
        self.assertEqual(parsed["douban_id"], "3000003")
        self.assertEqual(parsed["comment"], "真正的游戏短评")
        self.assertNotIn("游戏简介", parsed["comment"])

    def test_crawl_books_uses_query_parameter_for_pagination(self):
        urls = []

        def fake_get(url, timeout=30):
            urls.append(url)
            return DummyResponse("<html></html>")

        with patch.object(crawl_public, "USER_ID", "demo"), patch.object(
            crawl_public.SESSION, "get", side_effect=fake_get
        ):
            data = crawl_public.crawl_books()

        self.assertEqual(
            data, {"wish": [], "collect": [], "reading": []}
        )
        self.assertIn(
            "https://book.douban.com/people/demo/collect?start=0",
            urls,
        )
        self.assertIn(
            "https://book.douban.com/people/demo/reading?start=0",
            urls,
        )
        self.assertIn(
            "https://book.douban.com/people/demo/wish?start=0",
            urls,
        )
        self.assertNotIn(
            "https://book.douban.com/people/demo/collect&start=0",
            urls,
        )


if __name__ == "__main__":
    unittest.main()
