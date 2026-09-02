import unittest
from pathlib import Path


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
        # 游戏条目的简介和短评在同一块里，简介不能混进短评。
        self.assertNotIn("游戏简介", item["comment"])

    def test_music_comment_without_comment_class(self):
        """音乐评语在 info 列表最后一个没有 class 的 li 里。"""
        item = self.parse_fixture(MusicCrawler, "music_collection_item_plain_li.html")
        self.assertEqual(item["comment"], "没有 class 的音乐评语")
        # 标题、艺术家、评分不能被评语提取带偏。
        self.assertEqual(item["title"], "测试专辑")
        self.assertEqual(item["artist"], "测试音乐人")
        self.assertEqual(item["rating"], "5")

    def test_music_without_comment_stays_empty(self):
        """没写评语时不能把日期/评分那一行当成评语。"""
        item = self.parse_fixture(MusicCrawler, "music_collection_item_no_comment.html")
        self.assertEqual(item["comment"], "")

    def test_game_comment_without_comment_class(self):
        """游戏评语在条目末尾一个没有 class 的 p 里。"""
        item = self.parse_fixture(GameCrawler, "game_collection_item_plain_p.html")
        self.assertEqual(item["comment"], "没有 class 的游戏评语")
        self.assertNotIn("游戏简介", item["comment"])

    def test_game_title_not_overwritten_by_rating_title(self):
        """评分只以 title="力荐" 给出时，条目标题不能被评分说法覆盖。"""
        item = self.parse_fixture(GameCrawler, "game_collection_item_plain_p.html")
        self.assertEqual(item["title"], "测试游戏")
        self.assertEqual(item["rating"], "5")

    def test_game_without_comment_stays_empty(self):
        """没写评语时游戏简介不能顶替评语。"""
        item = self.parse_fixture(GameCrawler, "game_collection_item_no_comment.html")
        self.assertEqual(item["comment"], "")


if __name__ == "__main__":
    unittest.main()
