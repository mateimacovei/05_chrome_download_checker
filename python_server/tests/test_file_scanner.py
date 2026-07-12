import unittest

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


if __name__ == "__main__":
    unittest.main()
