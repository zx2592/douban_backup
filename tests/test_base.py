import tempfile
import unittest
from unittest.mock import Mock, patch

from backup_state import BackupState
from base import BaseCrawler
from books import BookCrawler
from config import DELAY_BETWEEN_REQUESTS
from games import GameCrawler
from movies import MovieCrawler
from music import MusicCrawler


class DummyResponse:
    def __init__(self, text="", status_code=200, url="https://example.test/page"):
        self.text = text
        self.status_code = status_code
        self.url = url


class DummyCrawler(BaseCrawler):
    def __init__(self, session, state_store=None, items=None, next_url=None):
        super().__init__(session, category_key="movies", state_store=state_store)
        self.items = list(items or [])
        self.next_url = next_url

    def _parse_items(self, response, collection_type=None):
        return list(self.items)

    def _get_pagination(self, response):
        return self.next_url


class BaseCrawlerTests(unittest.TestCase):
    @patch("base.time.sleep")
    def test_uses_configured_request_delay(self, sleep):
        session = Mock()
        response = DummyResponse()
        session.get.return_value = response
        crawler = DummyCrawler(session)
        crawler.request_delay = 4.5

        self.assertIs(crawler._make_request("https://example.test/delayed"), response)

        sleep.assert_called_once_with(4.5)

    @patch("base.time.sleep")
    def test_not_found_response_is_not_retried(self, _sleep):
        session = Mock()
        response = DummyResponse(status_code=404)
        session.get.return_value = response
        crawler = DummyCrawler(session)

        self.assertIs(crawler._make_request("https://example.test/missing"), response)
        session.get.assert_called_once()

    @patch("base.time.sleep")
    def test_server_error_is_retried(self, _sleep):
        session = Mock()
        response = DummyResponse(status_code=503)
        session.get.return_value = response
        crawler = DummyCrawler(session)

        self.assertIs(crawler._make_request("https://example.test/error"), response)
        self.assertEqual(session.get.call_count, 3)

    @patch("base.time.sleep")
    def test_full_page_without_pagination_keeps_checkpoint_incomplete(self, _sleep):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = BackupState(tmpdir, user_id="demo")
            session = Mock()
            session.get.return_value = DummyResponse("<html><body></body></html>")
            crawler = DummyCrawler(
                session,
                state_store=state,
                items=[{"title": str(index)} for index in range(15)],
            )

            result = crawler.crawl_collection("https://example.test/page", "collect")

            self.assertEqual(result, [])
            self.assertFalse(state.is_collection_complete("movies", "collect"))
            self.assertEqual(
                state.get_resume_url("movies", "collect"),
                "https://example.test/page",
            )

    @patch("base.time.sleep")
    def test_short_page_is_marked_complete(self, _sleep):
        with tempfile.TemporaryDirectory() as tmpdir:
            state = BackupState(tmpdir, user_id="demo")
            session = Mock()
            session.get.return_value = DummyResponse("<html><body></body></html>")
            crawler = DummyCrawler(
                session,
                state_store=state,
                items=[{"title": "only item"}],
            )

            result = crawler.crawl_collection("https://example.test/page", "collect")

            self.assertEqual(len(result), 1)
            self.assertTrue(state.is_collection_complete("movies", "collect"))


class CrawlerRequestDelayTests(unittest.TestCase):
    CRAWLER_CLASSES = (MovieCrawler, BookCrawler, MusicCrawler, GameCrawler)

    def test_crawlers_accept_custom_request_delay(self):
        for crawler_class in self.CRAWLER_CLASSES:
            with self.subTest(crawler=crawler_class.__name__):
                crawler = crawler_class(
                    session=None,
                    state_store=None,
                    request_delay=4.5,
                )
                self.assertEqual(crawler.request_delay, 4.5)

    def test_crawlers_fall_back_to_default_request_delay(self):
        for crawler_class in self.CRAWLER_CLASSES:
            with self.subTest(crawler=crawler_class.__name__):
                crawler = crawler_class(session=None, request_delay=None)
                self.assertEqual(crawler.request_delay, DELAY_BETWEEN_REQUESTS)


if __name__ == "__main__":
    unittest.main()


class PagedCrawler(BaseCrawler):
    """按预设页序返回条目的爬虫，用于验证增量模式下的翻页与早停。"""

    def __init__(self, session, pages, state_store=None, baseline=None, incremental=False):
        super().__init__(
            session,
            category_key="movies",
            state_store=state_store,
            baseline=baseline,
            incremental=incremental,
        )
        self.pages = list(pages)
        self.page_index = 0
        self.requested_urls = []

    def _make_request(self, url):
        self.requested_urls.append(url)
        return DummyResponse(url=url)

    def _parse_items(self, response, collection_type=None):
        if self.page_index >= len(self.pages):
            return []
        items = self.pages[self.page_index]
        self.page_index += 1
        return list(items)

    def _get_pagination(self, response):
        return (
            f"https://example.test/page{self.page_index}"
            if self.page_index < len(self.pages)
            else None
        )

    def _is_last_page(self, response, items):
        return self.page_index >= len(self.pages)


def _movie(douban_id, rating="5"):
    return {
        "douban_id": douban_id,
        "title": f"片{douban_id}",
        "rating": rating,
        "comment": "",
        "date": "2026-01-01",
    }


class IncrementalCrawlTests(unittest.TestCase):
    def _baseline(self, tmpdir, items):
        from incremental import Baseline

        baseline = Baseline(tmpdir, user_id="demo")
        baseline.update("movies", "collect", items)
        return baseline

    def test_without_baseline_crawls_every_page(self):
        pages = [[_movie("5"), _movie("4")], [_movie("3")], [_movie("2"), _movie("1")]]
        crawler = PagedCrawler(Mock(), pages)

        result = crawler.crawl_collection("https://example.test/page0", "collect")

        self.assertEqual(5, len(result))
        self.assertEqual(3, len(crawler.requested_urls))
        self.assertFalse(crawler.stopped_at_baseline)

    def test_stops_paging_once_baseline_is_reached(self):
        old = [_movie("3"), _movie("2"), _movie("1")]
        pages = [[_movie("5"), _movie("4")], [_movie("3"), _movie("2")], [_movie("1")]]

        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = PagedCrawler(
                Mock(), pages, baseline=self._baseline(tmpdir, old), incremental=True
            )
            result = crawler.crawl_collection("https://example.test/page0", "collect")

        # 第二页一开头就撞上基线，第三页不该再请求。
        self.assertEqual(2, len(crawler.requested_urls))
        self.assertTrue(crawler.stopped_at_baseline)
        self.assertFalse(crawler.incomplete)
        # 合并后仍是完整的 5 条，顺序为新条目在前。
        self.assertEqual(
            ["5", "4", "3", "2", "1"], [item["douban_id"] for item in result]
        )

    def test_reaching_baseline_is_not_treated_as_incomplete(self):
        """撞上基线是正常结束，不能被当成抓取中断而保留断点。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            state = BackupState(tmpdir, user_id="demo")
            crawler = PagedCrawler(
                Mock(),
                [[_movie("2"), _movie("1")]],
                state_store=state,
                baseline=self._baseline(tmpdir, [_movie("1")]),
                incremental=True,
            )
            crawler.crawl_collection("https://example.test/page0", "collect")

            self.assertFalse(crawler.incomplete)
            self.assertFalse(state.has_incomplete_collections())

    def test_edited_item_is_refetched_and_replaces_baseline_copy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = self._baseline(tmpdir, [_movie("2", rating="3"), _movie("1")])
            crawler = PagedCrawler(
                Mock(),
                [[_movie("2", rating="5"), _movie("1")]],
                baseline=baseline,
                incremental=True,
            )
            result = crawler.crawl_collection("https://example.test/page0", "collect")

        self.assertEqual(2, len(result))
        self.assertEqual("2", result[0]["douban_id"])
        self.assertEqual("5", result[0]["rating"])

    def test_nothing_new_returns_baseline_unchanged(self):
        old = [_movie("2"), _movie("1")]
        with tempfile.TemporaryDirectory() as tmpdir:
            crawler = PagedCrawler(
                Mock(), [list(old)], baseline=self._baseline(tmpdir, old), incremental=True
            )
            result = crawler.crawl_collection("https://example.test/page0", "collect")

        self.assertEqual(old, result)
        self.assertEqual(0, crawler.fetched_count)

    def test_incremental_without_baseline_object_degrades_to_full_crawl(self):
        crawler = PagedCrawler(Mock(), [[_movie("1")]], baseline=None, incremental=True)

        self.assertFalse(crawler.incremental)
