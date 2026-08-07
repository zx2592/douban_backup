import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from books import BookCrawler
from games import GameCrawler
from movies import MovieCrawler
from music import MusicCrawler


class DummyResponse:
    def __init__(self, text):
        self.text = text


class CollectionParserTests(unittest.TestCase):
    FIXTURE_DIR = Path(__file__).parent / "fixtures"

    def parse_fixture(self, crawler_class, filename, collection="collect"):
        html = (self.FIXTURE_DIR / filename).read_text(encoding="utf-8")
        crawler = crawler_class(session=None)
        return crawler._parse_items(DummyResponse(html), collection)[0]

    def test_movie_comment_fixture(self):
        item = self.parse_fixture(MovieCrawler, "movie_collection_item.html")
        self.assertEqual(item["comment"], "值得反复观看")

    def test_book_comment_fixture(self):
        item = self.parse_fixture(BookCrawler, "book_collection_item.html")
        self.assertEqual(item["comment"], "标签不是 p 也应抓到")

    def test_music_comment_fixture(self):
        item = self.parse_fixture(MusicCrawler, "music_collection_item.html")
        self.assertEqual(item["comment"], "日期同节点的音乐短评")

    def test_game_comment_fixture_excludes_description(self):
        item = self.parse_fixture(GameCrawler, "game_collection_item.html")
        self.assertEqual(item["douban_id"], "3000003")
        self.assertEqual(item["comment"], "真正的游戏短评")
        self.assertNotIn("游戏简介", item["comment"])


if __name__ == "__main__":
    unittest.main()
