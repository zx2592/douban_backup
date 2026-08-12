import tempfile
import unittest
from unittest.mock import Mock, patch

from backup_state import BackupState
from base import BaseCrawler


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


if __name__ == "__main__":
    unittest.main()
