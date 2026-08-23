import json
import os
import tempfile
import unittest

from incremental import (
    Baseline,
    build_index,
    item_fingerprint,
    item_key,
    merge_items,
    take_until_known,
)


def movie(douban_id, title="片", rating="5", comment="", date="2026-01-01"):
    return {
        "douban_id": douban_id,
        "title": title,
        "rating": rating,
        "comment": comment,
        "date": date,
    }


class ItemKeyTests(unittest.TestCase):
    def test_key_prefers_douban_id(self):
        self.assertEqual("id:123", item_key(movie("123")))

    def test_key_falls_back_to_title_without_id(self):
        self.assertEqual("title:无名", item_key(movie("", title="无名")))

    def test_id_and_title_keys_never_collide(self):
        self.assertNotEqual(item_key(movie("7")), item_key(movie("", title="7")))

    def test_fingerprint_tolerates_missing_fields(self):
        # 音乐条目没有 date 字段，缺失字段应视为空串而不是抛异常。
        fingerprint = item_fingerprint({"title": "专辑", "rating": "4"})
        self.assertEqual(("专辑", "4", "", "", ""), fingerprint)

    def test_fingerprint_changes_when_user_edits_rating(self):
        self.assertNotEqual(
            item_fingerprint(movie("1", rating="3")),
            item_fingerprint(movie("1", rating="5")),
        )


class TakeUntilKnownTests(unittest.TestCase):
    def test_empty_index_keeps_everything(self):
        page = [movie("1"), movie("2")]
        fresh, reached = take_until_known(page, {})
        self.assertEqual(page, fresh)
        self.assertFalse(reached)

    def test_stops_at_first_unchanged_known_item(self):
        known = movie("2")
        page = [movie("1"), known, movie("3")]
        fresh, reached = take_until_known(page, build_index([known]))
        self.assertEqual([movie("1")], fresh)
        self.assertTrue(reached)

    def test_edited_item_is_kept_and_scan_continues(self):
        """用户改评分会让旧条目重新排到最前面，不能因为 ID 眼熟就跳过。"""
        old = movie("1", rating="3")
        edited = movie("1", rating="5")
        page = [edited, movie("2")]

        fresh, reached = take_until_known(page, build_index([old]))

        self.assertEqual([edited, movie("2")], fresh)
        self.assertFalse(reached)

    def test_whole_page_known_returns_nothing(self):
        page = [movie("1"), movie("2")]
        fresh, reached = take_until_known(page, build_index(page))
        self.assertEqual([], fresh)
        self.assertTrue(reached)


class MergeItemsTests(unittest.TestCase):
    def test_fresh_items_come_first(self):
        merged = merge_items([movie("3")], [movie("2"), movie("1")])
        self.assertEqual(["id:3", "id:2", "id:1"], [item_key(i) for i in merged])

    def test_fresh_version_wins_over_baseline(self):
        merged = merge_items([movie("1", rating="5")], [movie("1", rating="3")])
        self.assertEqual(1, len(merged))
        self.assertEqual("5", merged[0]["rating"])

    def test_merge_is_idempotent(self):
        """断点标记完成后会用未合并的数据再合一次，重复合并不能产生重复条目。"""
        baseline = [movie("1"), movie("2")]
        once = merge_items([movie("3")], baseline)
        twice = merge_items([movie("3")], once)
        self.assertEqual(once, twice)

    def test_duplicate_fresh_items_are_deduped(self):
        merged = merge_items([movie("1"), movie("1")], [])
        self.assertEqual(1, len(merged))


class BaselineStoreTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = Baseline(tmpdir, user_id="demo")
            self.assertTrue(baseline.is_empty())

            baseline.update("movies", "collect", [movie("1")])
            baseline.save()

            reloaded = Baseline(tmpdir, user_id="demo")
            self.assertFalse(reloaded.is_empty())
            self.assertEqual([movie("1")], reloaded.get_items("movies", "collect"))
            self.assertEqual({"id:1"}, set(reloaded.index_for("movies", "collect")))

    def test_baseline_is_isolated_per_account(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mine = Baseline(tmpdir, user_id="demo")
            mine.update("movies", "collect", [movie("1")])
            mine.save()

            other = Baseline(tmpdir, user_id="someone-else")

            self.assertTrue(other.is_empty())
            self.assertNotEqual(mine.path, other.path)

    def test_corrupt_baseline_degrades_to_full_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = Baseline(tmpdir, user_id="demo")
            baseline.update("movies", "collect", [movie("1")])
            baseline.save()

            with open(baseline.path, "w", encoding="utf-8") as file_obj:
                file_obj.write("{ 这不是合法 JSON")

            reloaded = Baseline(tmpdir, user_id="demo")

            self.assertTrue(reloaded.is_empty())

    def test_mismatched_format_is_discarded(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = Baseline(tmpdir, user_id="demo")
            baseline.update("movies", "collect", [movie("1")])
            baseline.save()

            with open(baseline.path, "r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
            payload["format"] = 999
            with open(baseline.path, "w", encoding="utf-8") as file_obj:
                json.dump(payload, file_obj)

            self.assertTrue(Baseline(tmpdir, user_id="demo").is_empty())

    def test_save_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            baseline = Baseline(tmpdir, user_id="demo")
            baseline.update("movies", "collect", [movie("1")])
            baseline.save()

            leftovers = [n for n in os.listdir(tmpdir) if n.endswith(".tmp")]

        self.assertEqual([], leftovers)


if __name__ == "__main__":
    unittest.main()
