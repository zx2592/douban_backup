import unittest
from unittest.mock import Mock, patch

from auth import DoubanAuth
from books import BookCrawler
from games import GameCrawler
from main import DoubanBackup
from movies import MovieCrawler
from music import MusicCrawler


class BackupLoginTests(unittest.TestCase):
    def test_auth_exposes_no_password_login(self):
        """豆瓣登录页有滑块验证，表单式账号密码登录已失效并被移除。"""
        self.assertFalse(hasattr(DoubanAuth, "login"))
        self.assertTrue(hasattr(DoubanAuth, "login_with_cookies"))

    def test_cookie_login_fails_when_user_id_is_missing(self):
        backup = DoubanBackup()
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = True
        backup.auth.get_session.return_value = object()

        with patch.object(
            DoubanBackup, "_load_user_info", autospec=True, side_effect=lambda self: None
        ):
            result = backup._login()

        self.assertFalse(result)
        self.assertIsNone(backup.user_id)

    def test_login_fails_without_valid_cookies(self):
        backup = DoubanBackup()
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = False

        result = backup._login()

        self.assertFalse(result)
        self.assertIsNone(backup.user_id)
        self.assertIsNone(backup.session)

    def test_login_never_prompts_for_a_password(self):
        """账号密码登录已移除，登录流程不得再读取任何交互输入。"""
        backup = DoubanBackup()
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = False

        with patch("builtins.input", side_effect=AssertionError("不应提示输入账号")), patch(
            "getpass.getpass", side_effect=AssertionError("不应提示输入密码")
        ):
            result = backup._login()

        self.assertFalse(result)
        backup.auth.login.assert_not_called()

    def test_login_succeeds_after_loading_user_id(self):
        backup = DoubanBackup()
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = True
        backup.auth.get_session.return_value = object()

        def load_user_info(instance):
            instance.user_id = "demo-user"

        with patch.object(
            DoubanBackup, "_load_user_info", autospec=True, side_effect=load_user_info
        ):
            result = backup._login()

        self.assertTrue(result)
        self.assertEqual("demo-user", backup.user_id)

    def test_backup_all_respects_selected_items(self):
        backup = DoubanBackup(selected_items=["movies", "music"])
        backup.session = object()
        backup.user_id = "demo"

        with patch("main.MovieCrawler") as movie_cls, patch(
            "main.BookCrawler"
        ) as book_cls, patch("main.MusicCrawler") as music_cls, patch(
            "main.GameCrawler"
        ) as game_cls:
            movie_cls.return_value.crawl_all_movies.return_value = {"collect": []}
            music_cls.return_value.crawl_all_music.return_value = {"collect": []}

            data = backup._backup_all()

        self.assertIn("movies", data)
        self.assertIn("music", data)
        self.assertNotIn("books", data)
        self.assertNotIn("games", data)
        movie_cls.return_value.crawl_all_movies.assert_called_once()
        music_cls.return_value.crawl_all_music.assert_called_once()
        book_cls.assert_not_called()
        game_cls.assert_not_called()

    def test_backup_all_builds_real_crawlers_with_request_delay(self):
        backup = DoubanBackup(request_delay=4.5)
        backup.session = object()
        backup.user_id = "demo"
        crawlers = []

        with patch.object(
            MovieCrawler, "crawl_all_movies", autospec=True,
            side_effect=lambda self: (crawlers.append(self), {"collect": []})[1],
        ), patch.object(
            BookCrawler, "crawl_all_books", autospec=True,
            side_effect=lambda self: (crawlers.append(self), {"collect": []})[1],
        ), patch.object(
            MusicCrawler, "crawl_all_music", autospec=True,
            side_effect=lambda self: (crawlers.append(self), {"collect": []})[1],
        ), patch.object(
            GameCrawler, "crawl_all_games", autospec=True,
            side_effect=lambda self: (crawlers.append(self), {"collect": []})[1],
        ):
            data = backup._backup_all()

        self.assertEqual(set(data), {"movies", "books", "music", "games"})
        self.assertEqual(len(crawlers), 4)
        for crawler in crawlers:
            self.assertEqual(crawler.request_delay, 4.5)

    def test_backup_category_saves_timestamped_files(self):
        """单分类备份必须写入带时间戳的文件，且 JSON 与 Excel 共用同一个时间戳。"""
        backup = DoubanBackup(selected_items=["movies"])
        backup.storage = Mock()
        backup.storage.backup_dir = "/tmp/backup"
        backup.storage.new_timestamp.return_value = "20260322_101500"

        with patch.object(
            DoubanBackup, "_login", autospec=True, return_value=True
        ), patch("main.MovieCrawler") as movie_cls:
            crawler = movie_cls.return_value
            crawler.crawl_all_movies.return_value = {"collect": []}
            crawler.incomplete = False

            backup.backup_category("movies")

        backup.storage.save_category_json.assert_called_once_with(
            {"collect": []}, "movies", timestamp="20260322_101500"
        )
        backup.storage.save_category_excel.assert_called_once_with(
            {"movies": {"collect": []}}, "movies", timestamp="20260322_101500"
        )
        backup.storage.save_json.assert_not_called()
        backup.storage.save_excel.assert_not_called()

    def test_full_backup_shares_one_timestamp(self):
        backup = DoubanBackup(selected_items=["movies"])
        backup.storage = Mock()
        backup.storage.backup_dir = "/tmp/backup"
        backup.storage.new_timestamp.return_value = "20260322_101500"

        with patch.object(
            DoubanBackup, "_login", autospec=True, return_value=True
        ), patch.object(
            DoubanBackup, "_backup_all", autospec=True, return_value={"movies": {}}
        ):
            backup.run()

        backup.storage.save_all_json.assert_called_once_with(
            {"movies": {}}, timestamp="20260322_101500"
        )
        backup.storage.save_all_excel.assert_called_once_with(
            {"movies": {}}, timestamp="20260322_101500"
        )

    def test_verify_reports_login_failure(self):
        backup = DoubanBackup()
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = False

        report = backup.verify()

        self.assertFalse(report["ok"])
        self.assertEqual(report["error_code"], "login_expired")

    def test_verify_reports_category_access(self):
        backup = DoubanBackup(selected_items=["movies", "books"])
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = True
        session = Mock()
        backup.auth.get_session.return_value = session

        class Response:
            def __init__(self, url, status_code=200, text="ok"):
                self.url = url
                self.status_code = status_code
                self.text = text

        def load_user_info(instance):
            instance.user_id = "demo-user"
            return {"id": "demo-user", "name": "Tester"}

        session.get.side_effect = [
            Response("https://movie.douban.com/people/demo-user/collect", 200, "ok"),
            Response("https://book.douban.com/people/demo-user/collect?start=0&type=book", 404, "页面不存在"),
        ]

        with patch.object(
            DoubanBackup, "_load_user_info", autospec=True, side_effect=load_user_info
        ):
            report = backup.verify()

        self.assertTrue(report["login_ok"])
        self.assertEqual(report["user"]["id"], "demo-user")
        self.assertEqual(report["checks"][0]["category"], "movies")
        self.assertEqual(report["checks"][0]["status"], "ok")
        self.assertEqual(report["checks"][1]["category"], "books")
        self.assertEqual(report["checks"][1]["status"], "error")


if __name__ == "__main__":
    unittest.main()
