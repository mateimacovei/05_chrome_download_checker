import unittest
from pathlib import Path


SOURCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SOURCE_DIR.parent

CONTENT_SCRIPTS = (
    "pixiv_script.js",
    "twitter_script.js",
    "twitter_single_image_script.js",
)


class PopupCompatibilityTests(unittest.TestCase):
    def test_popup_execute_script_uses_documented_func_key(self):
        source = (SOURCE_DIR / "popup.js").read_text(encoding="utf-8")

        self.assertEqual(source.count("func: setExtensionFixedViewAsHidden"), 1)
        self.assertEqual(source.count("func: setExtensionFixedViewAsVisible"), 1)
        self.assertNotIn("function:", source)


class BackendUrlTests(unittest.TestCase):
    def test_content_scripts_use_configured_backend_url_with_local_default(self):
        for script_name in CONTENT_SCRIPTS:
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertIn(
                    'const backendUrl = data.backendUrl || "http://localhost:8000";',
                    source,
                )
                self.assertNotIn('"http://localhost:8000/contains', source)

    def test_content_scripts_build_contains_endpoint_from_backend_url(self):
        expected_snippets = {
            "pixiv_script.js": 'loadImages.open("GET", backendUrl + "/contains?name=" + pictureSearch, true);',
            "twitter_script.js": 'loadImages.open("POST", backendUrl + "/contains", true);',
            "twitter_single_image_script.js": 'loadImages.open("GET", backendUrl + "/contains?name=" + imageInPage, true);',
        }

        for script_name, snippet in expected_snippets.items():
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")
                self.assertIn(snippet, source)


class ReadmeDocumentationTests(unittest.TestCase):
    def test_readme_documents_cross_browser_build_and_loading(self):
        source = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python browser_extension/build_extension.py", source)
        self.assertIn("dist/firefox", source)
        self.assertIn("dist/chrome", source)
        self.assertIn("about:debugging#/runtime/this-firefox", source)
        self.assertIn("chrome://extensions", source)
        self.assertIn("python -m uvicorn app:app --reload", source)


if __name__ == "__main__":
    unittest.main()
