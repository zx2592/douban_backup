import os
import tempfile
import unittest
from unittest.mock import patch

import config


class DataDirTests(unittest.TestCase):
    """Cookie 和备份该写到哪里，取决于是源码运行还是 pip 安装。"""

    def test_source_checkout_uses_the_project_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "pyproject.toml"), "w").close()
            with patch.object(config, "PROJECT_DIR", tmpdir), patch.dict(
                os.environ, {}, clear=True
            ):
                self.assertEqual(
                    os.path.join(tmpdir, "data"), config._resolve_data_dir()
                )

    def test_git_checkout_also_uses_the_project_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".git"))
            with patch.object(config, "PROJECT_DIR", tmpdir), patch.dict(
                os.environ, {}, clear=True
            ):
                self.assertEqual(
                    os.path.join(tmpdir, "data"), config._resolve_data_dir()
                )

    def test_installed_package_uses_the_home_directory(self):
        """装进 site-packages 后再往那里写，升级会被清掉，还可能是只读的。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(config, "PROJECT_DIR", tmpdir), patch.dict(
                os.environ, {}, clear=True
            ):
                resolved = config._resolve_data_dir()

        self.assertEqual(
            os.path.join(os.path.expanduser("~"), ".douban_backup"), resolved
        )
        self.assertNotIn("site-packages", resolved)

    def test_environment_variable_wins(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            open(os.path.join(tmpdir, "pyproject.toml"), "w").close()
            with patch.object(config, "PROJECT_DIR", tmpdir), patch.dict(
                os.environ, {"DOUBAN_BACKUP_HOME": "/tmp/somewhere"}, clear=True
            ):
                self.assertEqual("/tmp/somewhere", config._resolve_data_dir())

    def test_environment_variable_expands_user(self):
        with patch.dict(os.environ, {"DOUBAN_BACKUP_HOME": "~/backups"}, clear=True):
            resolved = config._resolve_data_dir()

        self.assertTrue(os.path.isabs(resolved))
        self.assertNotIn("~", resolved)


if __name__ == "__main__":
    unittest.main()
