import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PYTHON_SERVER_DIR = Path(__file__).resolve().parents[1]
if str(PYTHON_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_SERVER_DIR))

import file_scanner
from file_scanner import filter_config_for_os


class FilterConfigForOsTests(unittest.TestCase):
    def test_windows_keeps_only_drive_letter_paths(self):
        config = [
            {"folder": "E:\\01_Vault\\phone_DCIM", "recursive": True},
            {"folder": "D:/personal/Downloads/to phone", "recursive": True},
            {"folder": "/mnt/d/personal/Downloads/to phone", "recursive": True},
            {"folder": "relative/path", "recursive": True},
        ]

        filtered = filter_config_for_os(config, "nt")

        self.assertEqual(filtered, config[:2])

    def test_posix_keeps_only_absolute_unix_paths(self):
        config = [
            {"folder": "E:\\01_Vault\\phone_DCIM", "recursive": True},
            {"folder": "/mnt/d/personal/Downloads/to phone", "recursive": True},
            {"folder": "/home/user/downloads", "recursive": False},
            {"folder": "relative/path", "recursive": True},
        ]

        filtered = filter_config_for_os(config, "posix")

        self.assertEqual(filtered, config[1:3])


class ReadConfigAndGetFilesTests(unittest.TestCase):
    def test_loads_config_relative_to_module_when_cwd_is_elsewhere(self):
        expected_config_path = (
            Path(file_scanner.__file__).resolve().parent / "config" / "folders.json"
        )
        folder = "C:/Downloads" if os.name == "nt" else "/tmp/downloads"
        config = [{"folder": folder, "recursive": False}]
        scanned_files = [object()]

        actual_config_path = None
        original_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as other_cwd:
            try:
                os.chdir(other_cwd)
                with patch("file_scanner.load_json", return_value=config) as load_json:
                    with patch(
                        "file_scanner.recursive_get_files", return_value=scanned_files
                    ) as recursive_get_files:
                        files = file_scanner.read_config_and_get_files()
                        actual_config_path = Path(load_json.call_args.args[0]).resolve()
            finally:
                os.chdir(original_cwd)

        self.assertEqual(actual_config_path, expected_config_path)
        recursive_get_files.assert_called_once_with(folder, False)
        self.assertEqual(files, scanned_files)

    def test_skips_bad_configured_folder_and_scans_later_good_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_folder = Path(tmpdir) / "missing"
            good_folder = Path(tmpdir) / "good"
            good_folder.mkdir()
            (good_folder / "download.txt").write_text("contents")

            config = [
                {"folder": str(missing_folder), "recursive": True},
                {"folder": str(good_folder), "recursive": False},
            ]

            with patch("file_scanner.load_json", return_value=config), patch("builtins.print"):
                files = file_scanner.read_config_and_get_files()

        self.assertEqual([f.name for f in files], ["download.txt"])


class RecursiveGetFilesTests(unittest.TestCase):
    def test_missing_path_returns_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing"

            self.assertEqual(file_scanner.recursive_get_files(str(missing_path), True), [])

    def test_recursive_scan_does_not_duplicate_files_through_symlinked_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            real_dir = root / "real"
            real_dir.mkdir()
            (real_dir / "download.txt").write_text("contents")

            symlink_dir = root / "real-link"
            try:
                symlink_dir.symlink_to(real_dir, target_is_directory=True)
            except (NotImplementedError, OSError) as exc:
                self.skipTest(f"directory symlinks are unavailable: {exc}")

            files = file_scanner.recursive_get_files(str(root), True)

        self.assertEqual([f.name for f in files], ["download.txt"])


if __name__ == "__main__":
    unittest.main()
