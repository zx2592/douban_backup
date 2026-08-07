import unittest
from unittest.mock import patch

import file_security


class FileSecurityTests(unittest.TestCase):
    def test_restrict_file_permissions_uses_chmod_on_posix(self):
        with patch.object(file_security.os, "name", "posix"), patch.object(
            file_security.os, "chmod"
        ) as mock_chmod:
            result = file_security.restrict_file_permissions("cookies.json")

        self.assertTrue(result)
        mock_chmod.assert_called_once_with("cookies.json", 0o600)

    def test_restrict_file_permissions_uses_icacls_on_windows(self):
        with patch.object(file_security.os, "name", "nt"), patch(
            "file_security.getpass.getuser", return_value="tester"
        ), patch("file_security.subprocess.run") as mock_run:
            result = file_security.restrict_file_permissions("cookies.json")

        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)
        first_call = mock_run.call_args_list[0]
        second_call = mock_run.call_args_list[1]
        self.assertIn("/inheritance:r", first_call.args[0])
        self.assertIn("/grant:r", second_call.args[0])
        self.assertIn("tester:(R,W)", second_call.args[0])


if __name__ == "__main__":
    unittest.main()
