import tempfile
import unittest


class BackupStateTests(unittest.TestCase):
    def test_progress_persists_resume_url_and_partial_items(self):
        from backup_state import BackupState

        with tempfile.TemporaryDirectory() as tmpdir:
            state = BackupState(tmpdir)
            items = [{"title": "Movie A"}]

            state.update_progress(
                "movies",
                "collect",
                current_url="https://movie.douban.com/people/demo/collect?start=0",
                next_url="https://movie.douban.com/people/demo/collect?start=15",
                items=items,
            )

            reloaded = BackupState(tmpdir)
            self.assertEqual(
                reloaded.get_resume_url("movies", "collect"),
                "https://movie.douban.com/people/demo/collect?start=15",
            )
            self.assertEqual(
                reloaded.get_partial_items("movies", "collect"),
                items,
            )
            self.assertFalse(reloaded.is_collection_complete("movies", "collect"))

    def test_mark_collection_complete_clears_resume_url(self):
        from backup_state import BackupState

        with tempfile.TemporaryDirectory() as tmpdir:
            state = BackupState(tmpdir)
            items = [{"title": "Movie A"}, {"title": "Movie B"}]

            state.mark_complete("movies", "collect", items)

            reloaded = BackupState(tmpdir)
            self.assertTrue(reloaded.is_collection_complete("movies", "collect"))
            self.assertIsNone(reloaded.get_resume_url("movies", "collect"))
            self.assertEqual(
                reloaded.get_partial_items("movies", "collect"),
                items,
            )


if __name__ == "__main__":
    unittest.main()
