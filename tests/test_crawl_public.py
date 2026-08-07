import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

import crawl_public


class DummyResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


class CrawlPublicTests(unittest.TestCase):
    def test_parse_book_item_reads_comment_from_any_comment_element(self):
        item = BeautifulSoup(
            '''<li class="subject-item"><div class="info">
            <h2><a href="https://book.douban.com/subject/1/">Book</a></h2>
            <span class="comment">A book comment</span>
            </div></li>''',
            "html.parser",
        ).li

        self.assertEqual(crawl_public.parse_book_item(item)["comment"], "A book comment")

    def test_parse_music_item_keeps_comment_next_to_date(self):
        item = BeautifulSoup(
            '''<div class="item"><div class="info"><ul>
            <li class="title"><a href="https://music.douban.com/subject/2/"><em>Album</em></a></li>
            <li class="intro">Artist / Album</li>
            <li><span class="date">2026-01-01</span><span class="comment">Music comment</span></li>
            </ul></div></div>''',
            "html.parser",
        ).div

        self.assertEqual(crawl_public.parse_music_item(item)["comment"], "Music comment")

    def test_parse_game_item_reads_only_comment(self):
        item = BeautifulSoup(
            '''<div class="common-item"><div class="info">
            <div class="title"><a href="https://www.douban.com/game/1">Game</a></div>
            <div class="desc">2026-01-01 / description</div>
            <span class="comment">Game comment</span>
            </div></div>''',
            "html.parser",
        ).div

        self.assertEqual(crawl_public.parse_game_item(item)["comment"], "Game comment")

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
