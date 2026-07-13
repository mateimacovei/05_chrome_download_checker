import asyncio
import importlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PYTHON_SERVER_DIR = Path(__file__).resolve().parents[1]
if str(PYTHON_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_SERVER_DIR))

from file_scanner import MyFile


def import_app_with_files(files):
    sys.modules.pop("app", None)
    with patch("file_scanner.read_config_and_get_files", return_value=files):
        return importlib.import_module("app")


class RefreshFilesTests(unittest.TestCase):
    def test_refresh_updates_file_index_used_by_all_and_contains_routes(self):
        old_files = [MyFile("/old", "stale_match.txt")]
        refreshed_files = [MyFile("/new", "fresh_match.txt")]
        app = import_app_with_files(old_files)
        self.addCleanup(lambda: sys.modules.pop("app", None))

        app.files_found = old_files

        with patch.object(app, "read_config_and_get_files", return_value=refreshed_files):
            self.assertEqual(asyncio.run(app.refresh_files()), refreshed_files)

        self.assertEqual(asyncio.run(app.get_all()), refreshed_files)
        self.assertEqual(asyncio.run(app.find_file_name_containing("fresh_match")), refreshed_files)
        self.assertEqual(asyncio.run(app.find_file_name_containing("stale_match")), [])
        self.assertEqual(
            asyncio.run(app.find_file_name_containing_str_in_list(["fresh_match"])),
            refreshed_files,
        )
        self.assertEqual(
            asyncio.run(app.find_file_name_containing_str_in_list(["stale_match"])),
            [],
        )


if __name__ == "__main__":
    unittest.main()
