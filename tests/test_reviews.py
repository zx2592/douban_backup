import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from reviews import ReviewCrawler
from storage import is_flat_category

FIXTURE_DIR = Path(__file__).parent / "fixtures"


class DummyResponse:
    def __init__(self, text, status_code=200, url="https://www.douban.com/x"):
        self.text = text
        self.status_code = status_code
        self.url = url


def fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding="utf-8")


class ReviewParsingTests(unittest.TestCase):
    def parse(self):
        crawler = ReviewCrawler(session=None)
        return crawler._parse_items(DummyResponse(fixture("review_list_item.html")))

    def test_parses_every_review_on_the_page(self):
        self.assertEqual(2, len(self.parse()))

    def test_uses_the_review_id_not_the_subject_id(self):
        """同一部片子可以写多篇长评，用被评对象的 ID 会让它们互相覆盖。"""
        first = self.parse()[0]

        self.assertEqual("14000001", first["douban_id"])
        self.assertEqual("1292052", first["subject_id"])

    def test_captures_title_subject_rating_and_date(self):
        first = self.parse()[0]

        self.assertEqual("关于希望的一点想法", first["title"])
        self.assertEqual("肖申克的救赎", first["subject"])
        self.assertEqual("5", first["rating"])
        self.assertEqual("2026-03-01 20:15:00", first["date"])

    def test_trailing_arrow_is_stripped_from_the_subject(self):
        self.assertNotIn(">", self.parse()[0]["subject"])

    def test_body_goes_into_comment_without_the_expand_control(self):
        """正文放进 comment，增量指纹和 Excel 列才能直接复用。"""
        body = self.parse()[0]["comment"]

        self.assertIn("每次都有新的体会", body)
        self.assertNotIn("展开", body)

    def test_records_the_full_url_and_site_type(self):
        movie_review, book_review = self.parse()

        self.assertEqual(
            "https://movie.douban.com/review/14000001/", movie_review["url"]
        )
        self.assertEqual("movie", movie_review["site_type"])
        self.assertEqual("book", book_review["site_type"])

    def test_ratings_from_allstar_classes(self):
        self.assertEqual("4", self.parse()[1]["rating"])


class FullTextTests(unittest.TestCase):
    def _crawler(self, response):
        crawler = ReviewCrawler(session=Mock(), fetch_full_text=True)
        crawler.request_delay = 0
        return crawler, patch.object(
            ReviewCrawler, "_make_request", autospec=True, return_value=response
        )

    def test_full_text_replaces_the_excerpt(self):
        crawler, patcher = self._crawler(DummyResponse(fixture("review_full_page.html")))
        with patcher:
            items = crawler._parse_items(DummyResponse(fixture("review_list_item.html")))

        self.assertIn("第二段正文", items[0]["comment"])

    def test_failed_full_text_keeps_the_excerpt(self):
        """单篇正文抓不到时保留摘要，不该让整次备份丢内容。"""
        crawler, patcher = self._crawler(None)
        with patcher:
            items = crawler._parse_items(DummyResponse(fixture("review_list_item.html")))

        self.assertIn("每次都有新的体会", items[0]["comment"])

    def test_excerpt_only_by_default(self):
        """默认不抓正文：每篇长评要额外一次请求，不能悄悄加上。"""
        crawler = ReviewCrawler(session=Mock())
        with patch.object(ReviewCrawler, "_make_request", autospec=True) as request:
            crawler._parse_items(DummyResponse(fixture("review_list_item.html")))

        request.assert_not_called()


class ReviewShapeTests(unittest.TestCase):
    def test_reviews_use_a_single_pseudo_collection(self):
        """长评没有想看/看过这类状态，用单个 collect 承载全部内容。"""
        crawler = ReviewCrawler(session=Mock())
        crawler.set_user_id("demo")
        with patch.object(
            ReviewCrawler, "crawl_collection", autospec=True, return_value=[{"a": 1}]
        ):
            result = crawler.crawl_all_reviews()

        self.assertEqual({"collect": [{"a": 1}]}, result)

    def test_reviews_are_a_flat_category(self):
        self.assertTrue(is_flat_category("reviews"))
        self.assertFalse(is_flat_category("movies"))

    def test_page_size_matches_the_review_list(self):
        # 长评列表每页 10 篇，用 15 会让"不足一页即末页"的判断提前触发。
        self.assertEqual(10, ReviewCrawler.PAGE_SIZE)


if __name__ == "__main__":
    unittest.main()
