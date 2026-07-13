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
        self.assertEqual(chrome_manifest["host_permissions"], ["http://localhost/*"])
        self.assertEqual(firefox_manifest["host_permissions"], ["http://localhost/*"])
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
            self.assertTrue((output_dir / "content_common.js").is_file())
            self.assertTrue((output_dir / "popup.html").is_file())
            self.assertTrue((output_dir / "popup.js").is_file())
            self.assertTrue((output_dir / "pixiv_script.js").is_file())
            self.assertTrue((output_dir / "twitter_script.js").is_file())
            self.assertTrue((output_dir / "twitter_single_image_script.js").is_file())
            self.assertTrue((output_dir / "pic_extension.css").is_file())
            self.assertTrue((output_dir / "images" / "resources" / "reload_icon.png").is_file())
            self.assertFalse((output_dir / "manifest.chrome.json").exists())
            self.assertFalse((output_dir / "manifest.firefox.json").exists())

    def test_generated_manifests_support_x_status_pages(self):
        build_extension.build_all(self.output_root)

        for browser in ("chrome", "firefox"):
            with self.subTest(browser=browser):
                manifest = json.loads(
                    (self.output_root / browser / "manifest.json").read_text(encoding="utf-8")
                )
                twitter_scripts = [
                    script
                    for script in manifest["content_scripts"]
                    if "twitter_script.js" in script.get("js", [])
                ]
                self.assertEqual(len(twitter_scripts), 1)
                self.assertIn("https://x.com/*/status/*", twitter_scripts[0]["matches"])

                resource_matches = [
                    match
                    for resource in manifest["web_accessible_resources"]
                    for match in resource["matches"]
                ]
                self.assertIn("https://x.com/*", resource_matches)

    def test_generated_manifests_allow_configurable_localhost_backend_ports(self):
        build_extension.build_all(self.output_root)

        configured_backend_url = "http://localhost:8123/contains"
        for browser in ("chrome", "firefox"):
            with self.subTest(browser=browser):
                manifest = json.loads(
                    (self.output_root / browser / "manifest.json").read_text(encoding="utf-8")
                )
                host_permissions = manifest["host_permissions"]
                self.assertNotIn("<all_urls>", host_permissions)
                self.assertNotIn("http://localhost:8000/*", host_permissions)
                self.assertIn(
                    "http://localhost/*",
                    host_permissions,
                    msg=f"{browser} permissions must cover {configured_backend_url}",
                )

    def test_generated_manifests_load_common_script_before_page_scripts(self):
        build_extension.build_all(self.output_root)

        expected_script_lists = {
            ("https://www.pixiv.net/en/artworks/*",): [
                "content_common.js",
                "pixiv_script.js",
            ],
            ("https://twitter.com/*/status/*", "https://x.com/*/status/*"): [
                "content_common.js",
                "twitter_script.js",
            ],
            ("https://pbs.twimg.com/*",): [
                "content_common.js",
                "twitter_single_image_script.js",
            ],
        }
        for browser in ("chrome", "firefox"):
            with self.subTest(browser=browser):
                manifest = json.loads(
                    (self.output_root / browser / "manifest.json").read_text(encoding="utf-8")
                )
                scripts_by_matches = {
                    tuple(script["matches"]): script["js"]
                    for script in manifest["content_scripts"]
                }
                for matches, script_list in expected_script_lists.items():
                    self.assertEqual(scripts_by_matches[matches], script_list)

    def test_build_uses_explicit_shared_file_allowlist(self):
        unreferenced_script = build_extension.SOURCE_DIR / "unreferenced_build_input.js"
        unreferenced_script.write_text("console.log('not part of the extension');\n", encoding="utf-8")
        self.addCleanup(unreferenced_script.unlink, missing_ok=True)

        build_extension.build_all(self.output_root)

        expected_files = {
            "background.js",
            "button.css",
            "content_common.js",
            "manifest.json",
            "options.html",
            "options.js",
            "pic_extension.css",
            "pixiv_script.js",
            "popup.html",
            "popup.js",
            "twitter_script.js",
            "twitter_convert_to_png.js",
            "twitter_single_image_script.js",
        }
        for browser in ("chrome", "firefox"):
            with self.subTest(browser=browser):
                copied_files = {
                    path.name
                    for path in (self.output_root / browser).iterdir()
                    if path.is_file()
                }
                self.assertEqual(copied_files, expected_files)


if __name__ == "__main__":
    unittest.main()
