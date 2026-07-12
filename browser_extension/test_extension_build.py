import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_extension


class ExtensionBuildTests(unittest.TestCase):
    def setUp(self):
        self.output_root = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.output_root)

    def test_build_creates_browser_outputs_with_correct_manifests(self):
        build_extension.build_all(self.output_root)

        chrome_dir = self.output_root / "chrome"
        firefox_dir = self.output_root / "firefox"
        chrome_manifest = json.loads((chrome_dir / "manifest.json").read_text(encoding="utf-8"))
        firefox_manifest = json.loads((firefox_dir / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(chrome_manifest["background"], {"service_worker": "background.js"})
        self.assertEqual(firefox_manifest["background"], {"scripts": ["background.js"]})
        self.assertEqual(chrome_manifest["host_permissions"], ["http://localhost:8000/*"])
        self.assertEqual(firefox_manifest["host_permissions"], ["http://localhost:8000/*"])
        self.assertEqual(
            firefox_manifest["browser_specific_settings"]["gecko"]["data_collection_permissions"],
            {"required": ["none"]},
        )
        self.assertEqual(
            firefox_manifest["browser_specific_settings"]["gecko"]["id"],
            "chrome-pic-finder@example.local",
        )

        for output_dir in (chrome_dir, firefox_dir):
            self.assertTrue((output_dir / "background.js").is_file())
            self.assertTrue((output_dir / "popup.html").is_file())
            self.assertTrue((output_dir / "popup.js").is_file())
            self.assertTrue((output_dir / "pixiv_script.js").is_file())
            self.assertTrue((output_dir / "twitter_script.js").is_file())
            self.assertTrue((output_dir / "twitter_single_image_script.js").is_file())
            self.assertTrue((output_dir / "pic_extension.css").is_file())
            self.assertTrue((output_dir / "images" / "resources" / "reload_icon.png").is_file())
            self.assertFalse((output_dir / "manifest.chrome.json").exists())
            self.assertFalse((output_dir / "manifest.firefox.json").exists())


if __name__ == "__main__":
    unittest.main()
