import unittest

from cli import exit_code


class ExitCodeTests(unittest.TestCase):
    """两个入口此前都丢弃返回值，失败时退出码也是 0，脚本无法判断成败。"""

    def test_failed_backup_exits_nonzero(self):
        self.assertEqual(1, exit_code(False))

    def test_successful_backup_exits_zero(self):
        self.assertEqual(0, exit_code(True))

    def test_none_is_a_failure(self):
        # 公开模式下用户 ID 为空时 main() 返回 None。
        self.assertEqual(1, exit_code(None))

    def test_verify_report_follows_its_ok_flag(self):
        self.assertEqual(0, exit_code({"ok": True, "checks": []}))
        self.assertEqual(1, exit_code({"ok": False, "error_code": "login_expired"}))

    def test_public_backup_result_follows_its_ok_flag(self):
        self.assertEqual(0, exit_code({"ok": True, "data": {}}))
        self.assertEqual(1, exit_code({"ok": False, "data": {}}))

    def test_backup_listing_exits_zero(self):
        # list 命令返回文件列表，空列表也不算失败。
        self.assertEqual(0, exit_code([]))
        self.assertEqual(0, exit_code([{"name": "douban_backup.json"}]))


if __name__ == "__main__":
    unittest.main()
