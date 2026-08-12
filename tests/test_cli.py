import unittest
from unittest.mock import patch

import main


class CliDispatchTests(unittest.TestCase):
    def test_main_dispatches_verify_command(self):
        with patch("main.DoubanBackup") as backup_cls:
            instance = backup_cls.return_value
            main.main(["verify"])

        instance.verify.assert_called_once()

    def test_main_dispatches_music_category(self):
        with patch("main.DoubanBackup") as backup_cls:
            instance = backup_cls.return_value
            main.main(["music"])

        instance.backup_category.assert_called_once_with("music")

    def test_main_dispatches_games_category(self):
        with patch("main.DoubanBackup") as backup_cls:
            instance = backup_cls.return_value
            main.main(["games"])

        instance.backup_category.assert_called_once_with("games")

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
            request_delay=None,
        )

    def test_main_passes_custom_request_delay_to_backup(self):
        with patch("main.DoubanBackup") as backup_cls:
            instance = backup_cls.return_value
            main.main(["--delay", "4.5"])

        backup_cls.assert_called_once_with(
            selected_items=["movies", "books", "music", "games"],
            output_dir=None,
            checkpoint_enabled=True,
            request_delay=4.5,
        )
        instance.run.assert_called_once()

    def test_main_passes_custom_request_delay_to_public_backup(self):
        with patch("main.run_public_backup") as run_public:
            main.main(["--public", "demo-user", "--delay", "3"])

        run_public.assert_called_once_with(
            "demo-user",
            categories=["movies", "books", "music", "games"],
            output_dir=None,
            request_delay=3.0,
        )


if __name__ == "__main__":
    unittest.main()
