import unittest
from unittest.mock import patch

import main


class CliDispatchTests(unittest.TestCase):
    def test_main_dispatches_verify_command(self):
        with patch("main.DoubanBackup") as backup_cls:
            instance = backup_cls.return_value
            main.main(["verify"])

        instance.verify.assert_called_once()

    def test_main_dispatches_public_backup_with_filtered_categories(self):
        with patch("main.run_public_backup") as run_public:
            main.main(
                [
                    "--public",
                    "demo-user",
                    "--only",
                    "movies,books",
                    "--skip",
                    "books",
                    "--output",
                    "D:\\exports",
                ]
            )

        run_public.assert_called_once_with(
            "demo-user",
            categories=["movies"],
            output_dir="D:\\exports",
        )


if __name__ == "__main__":
    unittest.main()
