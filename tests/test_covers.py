import os
import tempfile
import unittest
from unittest.mock import Mock

from covers import CoverDownloader, cover_filename, is_allowed_cover_url


def response(content=b"\x89PNG-data", status_code=200):
    return Mock(status_code=status_code, content=content)


class CoverUrlTests(unittest.TestCase):
    def test_accepts_douban_image_hosts(self):
        self.assertTrue(is_allowed_cover_url("https://img1.doubanio.com/view/a.jpg"))
        self.assertTrue(is_allowed_cover_url("http://img9.doubanio.com/view/b.webp"))
        self.assertTrue(is_allowed_cover_url("https://www.douban.com/pics/c.png"))

    def test_rejects_other_hosts(self):
        """cover 是从页面里解析出来的，不限制主机等于让页面决定去请求谁。"""
        self.assertFalse(is_allowed_cover_url("https://evil.example.com/a.jpg"))
        self.assertFalse(is_allowed_cover_url("https://doubanio.com.evil.test/a.jpg"))

    def test_rejects_non_http_schemes(self):
        self.assertFalse(is_allowed_cover_url("file:///etc/passwd"))
        self.assertFalse(is_allowed_cover_url("ftp://img1.doubanio.com/a.jpg"))

    def test_rejects_empty(self):
        self.assertFalse(is_allowed_cover_url(""))
        self.assertFalse(is_allowed_cover_url(None))


class CoverFilenameTests(unittest.TestCase):
    def test_uses_douban_id_and_keeps_extension(self):
        name = cover_filename({"douban_id": "12345"}, "https://img1.doubanio.com/a.webp")
        self.assertEqual("12345.webp", name)

    def test_defaults_to_jpg_when_extension_is_unknown(self):
        name = cover_filename({"douban_id": "7"}, "https://img1.doubanio.com/view/abc")
        self.assertEqual("7.jpg", name)

    def test_title_never_reaches_the_filename(self):
        """标题来自页面，含 ../ 时会把文件写到目标目录之外。"""
        name = cover_filename(
            {"douban_id": "", "title": "../../etc/passwd"},
            "https://img1.doubanio.com/a.jpg",
        )

        self.assertNotIn("/", name)
        self.assertNotIn("..", name)
        self.assertTrue(name.endswith(".jpg"))

    def test_non_numeric_id_falls_back_to_a_url_digest(self):
        name = cover_filename(
            {"douban_id": "../evil"}, "https://img1.doubanio.com/a.jpg"
        )

        self.assertNotIn("/", name)
        self.assertNotIn("..", name)


class CoverDownloadTests(unittest.TestCase):
    ITEM = {"douban_id": "42", "cover": "https://img1.doubanio.com/view/x.jpg"}

    def _download(self, tmpdir, data, session=None):
        session = session or Mock(**{"get.return_value": response()})
        downloader = CoverDownloader(session, tmpdir, delay=0)
        stats = downloader.download_all(data)
        return stats, session

    def test_downloads_and_records_relative_path(self):
        item = dict(self.ITEM)
        with tempfile.TemporaryDirectory() as tmpdir:
            stats, _ = self._download(tmpdir, {"movies": {"collect": [item]}})
            written = os.path.join(tmpdir, "covers", "movies", "42.jpg")

            self.assertTrue(os.path.exists(written))
            self.assertEqual(1, stats["downloaded"])

        self.assertEqual(os.path.join("covers", "movies", "42.jpg"), item["cover_path"])

    def test_sends_a_referer_header(self):
        """豆瓣图床校验 Referer，不带这个头会直接 403。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            _, session = self._download(
                tmpdir, {"movies": {"collect": [dict(self.ITEM)]}}
            )

        headers = session.get.call_args.kwargs["headers"]
        self.assertIn("douban.com", headers["Referer"])

    def test_existing_file_is_not_downloaded_again(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self._download(tmpdir, {"movies": {"collect": [dict(self.ITEM)]}})
            stats, session = self._download(
                tmpdir, {"movies": {"collect": [dict(self.ITEM)]}}
            )

        self.assertEqual(0, stats["downloaded"])
        self.assertEqual(1, stats["skipped"])
        session.get.assert_not_called()

    def test_failed_download_is_counted_not_raised(self):
        """封面是附加内容，单张失败不该让整次备份垮掉。"""
        session = Mock(**{"get.side_effect": OSError("网络中断")})
        with tempfile.TemporaryDirectory() as tmpdir:
            stats, _ = self._download(
                tmpdir, {"movies": {"collect": [dict(self.ITEM)]}}, session=session
            )

        self.assertEqual(1, stats["failed"])

    def test_non_douban_url_is_rejected_without_a_request(self):
        item = {"douban_id": "9", "cover": "https://evil.example.com/x.jpg"}
        with tempfile.TemporaryDirectory() as tmpdir:
            stats, session = self._download(tmpdir, {"movies": {"collect": [item]}})

        self.assertEqual(1, stats["rejected"])
        session.get.assert_not_called()
        self.assertNotIn("cover_path", item)

    def test_empty_response_leaves_no_partial_file(self):
        session = Mock(**{"get.return_value": response(content=b"")})
        with tempfile.TemporaryDirectory() as tmpdir:
            stats, _ = self._download(
                tmpdir, {"movies": {"collect": [dict(self.ITEM)]}}, session=session
            )
            leftovers = []
            for root, _dirs, files in os.walk(tmpdir):
                leftovers.extend(f for f in files if f.endswith(".part"))

        self.assertEqual(1, stats["failed"])
        self.assertEqual([], leftovers)

    def test_items_without_a_cover_are_skipped(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stats, session = self._download(
                tmpdir, {"movies": {"collect": [{"douban_id": "1"}]}}
            )

        session.get.assert_not_called()
        self.assertEqual(0, stats["downloaded"])


if __name__ == "__main__":
    unittest.main()
