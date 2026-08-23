import csv
import os
import tempfile
import unittest

from cli import parse_formats
from storage import DataStorage

DATA = {
    "movies": {
        "collect": [
            {
                "douban_id": "1292052",
                "title": "肖申克的救赎",
                "rating": "5",
                "comment": "值得反复观看",
                "tags": "经典",
                "date": "2026-01-01",
                "type": "movie",
            }
        ],
        "do": [],
        "wish": [],
    },
    "reviews": {
        "collect": [
            {
                "douban_id": "900",
                "title": "关于希望",
                "subject": "肖申克的救赎",
                "rating": "5",
                "date": "2026-03-01",
                "comment": "第一段\n第二段",
                "url": "https://movie.douban.com/review/900/",
                "type": "review",
            }
        ]
    },
}


class FormatOptionTests(unittest.TestCase):
    def test_defaults_to_xlsx(self):
        self.assertEqual(["xlsx"], parse_formats(None))
        self.assertEqual(["xlsx"], parse_formats(""))

    def test_accepts_a_comma_separated_list(self):
        self.assertEqual(["xlsx", "csv"], parse_formats("csv,xlsx"))

    def test_all_expands_to_every_format(self):
        self.assertEqual(["xlsx", "csv", "md"], parse_formats("all"))

    def test_order_is_stable_regardless_of_input_order(self):
        self.assertEqual(parse_formats("md,csv"), parse_formats("csv,md"))

    def test_duplicates_are_collapsed(self):
        self.assertEqual(["csv"], parse_formats("csv,csv"))

    def test_unknown_format_is_rejected(self):
        with self.assertRaises(ValueError) as raised:
            parse_formats("pdf")

        self.assertIn("pdf", str(raised.exception))


class CsvExportTests(unittest.TestCase):
    def _export(self, tmpdir):
        storage = DataStorage(backup_dir=tmpdir)
        return storage.save_csv(DATA, "demo")

    def test_writes_one_file_per_category(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self._export(tmpdir)
            names = sorted(os.path.basename(p) for p in paths)

        self.assertEqual(["demo_movies.csv", "demo_reviews.csv"], names)

    def test_has_a_status_column_and_numeric_rating(self):
        """CSV 没有分组和多工作表，状态要单独占一列；评分保留数字便于统计。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = self._export(tmpdir)
            movies = next(p for p in paths if "movies" in p)
            with open(movies, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))

        self.assertEqual("状态", rows[0][0])
        self.assertEqual("看过", rows[1][0])
        self.assertIn("5", rows[1])
        self.assertNotIn("★★★★★", rows[1])

    def test_uses_a_bom_so_excel_shows_chinese_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            movies = next(p for p in self._export(tmpdir) if "movies" in p)
            with open(movies, "rb") as f:
                head = f.read(3)

        self.assertEqual(b"\xef\xbb\xbf", head)

    def test_formula_like_values_are_escaped(self):
        data = {"movies": {"collect": [{"title": "=SUM(1,1)", "douban_id": "1"}]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = DataStorage(backup_dir=tmpdir)
            path = storage.save_csv(data, "danger")[0]
            with open(path, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))

        self.assertIn("'=SUM(1,1)", rows[1])

    def test_link_column_holds_a_url(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            reviews = next(p for p in self._export(tmpdir) if "reviews" in p)
            with open(reviews, encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))

        self.assertIn("https://movie.douban.com/review/900/", rows[1])


class MarkdownExportTests(unittest.TestCase):
    def _render(self, tmpdir, data=None):
        storage = DataStorage(backup_dir=tmpdir)
        path = storage.save_markdown(data if data is not None else DATA, "demo")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def test_groups_by_category_and_status(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            text = self._render(tmpdir)

        self.assertIn("# 豆瓣备份", text)
        self.assertIn("## 电影（1 部）", text)
        self.assertIn("### 看过（1 部）", text)
        self.assertIn("## 长评（1 篇）", text)
        # 扁平分类不再套一层同名小标题。
        self.assertNotIn("### 长评", text)

    def test_entries_are_links_with_stars_and_comment(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            text = self._render(tmpdir)

        self.assertIn("[肖申克的救赎](https://movie.douban.com/subject/1292052/)", text)
        self.assertIn("★★★★★", text)
        self.assertIn("> 值得反复观看", text)

    def test_review_body_keeps_its_paragraphs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            text = self._render(tmpdir)

        self.assertIn("> 第一段", text)
        self.assertIn("> 第二段", text)

    def test_markdown_characters_in_titles_are_escaped(self):
        """标题来自页面，未转义的 * 或 [ 会把排版搞乱。"""
        data = {"movies": {"collect": [{"title": "*星号* [方括号]", "douban_id": "1"}]}}
        with tempfile.TemporaryDirectory() as tmpdir:
            text = self._render(tmpdir, data)

        self.assertIn("\\*星号\\*", text)
        self.assertIn("\\[方括号\\]", text)

    def test_empty_statuses_are_omitted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            text = self._render(tmpdir)

        self.assertNotIn("### 想看", text)


if __name__ == "__main__":
    unittest.main()
