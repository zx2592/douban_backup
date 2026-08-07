import unittest
from unittest.mock import Mock, patch

from main import DoubanBackup


class BackupLoginTests(unittest.TestCase):
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

    def test_password_login_fails_when_user_id_is_missing(self):
        backup = DoubanBackup()
        backup.auth = Mock()
        backup.auth.login_with_cookies.return_value = False
        backup.auth.login.return_value = True
        backup.auth.get_session.return_value = object()

        with patch("builtins.input", return_value="user@example.com"), patch(
            "getpass.getpass", return_value="secret"
        ), patch.object(
            DoubanBackup, "_load_user_info", autospec=True, side_effect=lambda self: None
        ):
            result = backup._login()

        self.assertFalse(result)
        self.assertIsNone(backup.user_id)

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
