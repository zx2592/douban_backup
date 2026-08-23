import unittest

from games import GameCrawler
from music import MusicCrawler


class DummyResponse:
    def __init__(self, text):
        self.text = text


def music_page(rating_markup):
    return f"""
    <div class="item">
      <div class="info">
        <a href="https://music.douban.com/subject/9001/"><em>专辑</em></a>
        {rating_markup}
        <li class="intro">某乐队 / 2026</li>
      </div>
    </div>
    """


def game_page(rating_markup):
    return f"""
    <div class="common-item">
      <div class="title"><a href="https://www.douban.com/game/8001/">游戏</a></div>
      {rating_markup}
      <div class="desc">2026-01-01 / 动作</div>
    </div>
    """


class MusicRatingTests(unittest.TestCase):
    def parse(self, rating_markup):
        crawler = MusicCrawler(session=None)
        return crawler._parse_items(DummyResponse(music_page(rating_markup)), "collect")[0]

    def test_reads_rating_when_it_is_the_only_class(self):
        self.assertEqual("5", self.parse('<span class="rating5-t"></span>')["rating"])

    def test_extra_classes_after_the_rating_are_harmless(self):
        self.assertEqual(
            "4", self.parse('<span class="rating4-t extra"></span>')["rating"]
        )

    def test_reads_rating_after_a_class_without_digits(self):
        """rating-star 不含数字，必须继续往后找而不是就此放弃。"""
        self.assertEqual(
            "3", self.parse('<span class="rating-star rating3-t"></span>')["rating"]
        )

    def test_missing_rating_is_empty(self):
        self.assertEqual("", self.parse("")["rating"])


class GameRatingTests(unittest.TestCase):
    def parse(self, rating_markup):
        crawler = GameCrawler(session=None)
        return crawler._parse_items(DummyResponse(game_page(rating_markup)), "collect")[0]

    def test_allstar_class_maps_to_star_count(self):
        self.assertEqual("4", self.parse('<span class="allstar40"></span>')["rating"])
        self.assertEqual("5", self.parse('<span class="allstar50"></span>')["rating"])

    def test_chinese_title_is_converted_to_a_number(self):
        """title 是"力荐"这类中文，原样写入的话导出 Excel 时会被静默丢弃。"""
        self.assertEqual(
            "5", self.parse('<span class="rating-star" title="力荐"></span>')["rating"]
        )
        self.assertEqual(
            "2", self.parse('<span class="rating-star" title="较差"></span>')["rating"]
        )

    def test_unknown_title_yields_empty_rating_not_chinese_text(self):
        parsed = self.parse('<span class="rating-star" title="莫名其妙"></span>')

        self.assertEqual("", parsed["rating"])

    def test_class_without_digits_yields_empty_rating(self):
        """allstar-hidden 之类不含可用数字的 class 应安全跳过，条目本身要保留。"""
        parsed = self.parse('<span class="allstar-hidden"></span>')

        self.assertEqual("8001", parsed["douban_id"])
        self.assertEqual("", parsed["rating"])


if __name__ == "__main__":
    unittest.main()
