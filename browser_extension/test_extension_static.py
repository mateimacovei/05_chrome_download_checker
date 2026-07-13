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


class BackendRequestRoutingTests(unittest.TestCase):
    def test_content_scripts_delegate_backend_requests_to_common_helper(self):
        expected_snippets = {
            "pixiv_script.js": (
                'method: "GET"',
                'path: "/contains"',
                'query: { name: pictureSearch }',
            ),
            "twitter_script.js": (
                'method: "POST"',
                'path: "/contains"',
                'body: imagesInPage',
            ),
            "twitter_single_image_script.js": (
                'method: "GET"',
                'path: "/contains"',
                'query: { name: imageInPage }',
            ),
        }

        for script_name, snippets in expected_snippets.items():
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertNotIn("XMLHttpRequest", source)
                self.assertNotIn("backendUrl", source)
                self.assertNotIn("chrome.runtime.sendMessage", source)
                self.assertIn("requestDownloadCheck({", source)
                for snippet in snippets:
                    self.assertIn(snippet, source)

    def test_common_content_script_delegates_backend_requests_to_background(self):
        source = (SOURCE_DIR / "content_common.js").read_text(encoding="utf-8")

        self.assertIn("downloadedFinderExtension", source)
        self.assertIn("function requestDownloadCheck(request, callback)", source)
        self.assertIn("chrome.runtime.sendMessage({", source)
        self.assertIn('type: "CHECK_DOWNLOADS"', source)
        self.assertIn("...request", source)
        self.assertIn("callback(null)", source)

    def test_common_content_script_delegates_navigation_to_background(self):
        source = (SOURCE_DIR / "content_common.js").read_text(encoding="utf-8")

        self.assertIn("function navigateToUrl(newUrl)", source)
        self.assertIn('type: "NAVIGATE"', source)
        self.assertIn("downloadedFinderExtension.navigateToUrl = navigateToUrl;", source)

    def test_background_owns_backend_url_and_fetches_download_checks(self):
        source = (SOURCE_DIR / "background.js").read_text(encoding="utf-8")

        self.assertIn('const DEFAULT_BACKEND_URL = "http://localhost:8000";', source)
        self.assertIn('if (request.type === "CHECK_DOWNLOADS")', source)
        self.assertIn('chrome.storage.sync.get(["backendUrl"],', source)
        self.assertIn('fetch(backendUrl + request.path + queryString, fetchOptions)', source)
        self.assertIn('sendResponse({ ok: true, data });', source)
        self.assertIn('sendResponse({ ok: false });', source)

    def test_backend_cors_is_not_broadly_enabled(self):
        source = (REPO_ROOT / "python_server" / "app.py").read_text(encoding="utf-8")

        self.assertNotIn("CORSMiddleware", source)
        self.assertNotIn('allow_origins=["*"]', source)
        self.assertNotIn("app.add_middleware(", source)

    def test_content_scripts_do_not_own_backend_url_or_local_default(self):
        for script_name in CONTENT_SCRIPTS:
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertNotIn('const backendUrl = data.backendUrl || "http://localhost:8000";', source)
                self.assertNotIn('"http://localhost:8000/contains', source)

    def test_content_scripts_do_not_build_contains_endpoint_directly(self):
        for script_name in CONTENT_SCRIPTS:
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertNotIn('loadImages.open("GET", backendUrl + "/contains', source)
                self.assertNotIn('loadImages.open("POST", backendUrl + "/contains', source)


class ExtensionOverlayLayoutTests(unittest.TestCase):
    def test_extension_overlay_styles_are_namespaced(self):
        css_source = (SOURCE_DIR / "pic_extension.css").read_text(encoding="utf-8")

        self.assertNotIn("div.fixed", css_source)
        self.assertNotIn("div.frame", css_source)
        self.assertIn(".downloaded-finder-fixed", css_source)
        self.assertIn(".downloaded-finder-frame", css_source)
        self.assertIn(".downloaded-finder-toolbar", css_source)
        self.assertIn(".downloaded-finder-png-button-container", css_source)

        for script_name in CONTENT_SCRIPTS:
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertNotIn("classList.add('fixed')", source)
                self.assertNotIn('classList.add("fixed")', source)
                self.assertNotIn("classList.add('frame')", source)
                self.assertNotIn('classList.add("frame")', source)
                self.assertIn("downloaded-finder-", source)

        converter_source = (SOURCE_DIR / "twitter_convert_to_png.js").read_text(encoding="utf-8")
        self.assertNotIn("classList.add('fixed')", converter_source)
        self.assertNotIn('classList.add("fixed")', converter_source)
        self.assertNotIn("classList.add('frame')", converter_source)
        self.assertNotIn('classList.add("frame")', converter_source)

    def test_finder_toolbar_uses_non_overflowing_layout(self):
        for script_name in CONTENT_SCRIPTS:
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertIn("topBarDiv.classList.add('downloaded-finder-top-bar');", source)
                self.assertIn("toolbarDiv.classList.add('downloaded-finder-toolbar');", source)
                self.assertNotIn("titleText.style.padding = '40px'", source)
                self.assertNotIn("titleText.style.float = 'left'", source)

    def test_twimg_png_button_is_rendered_inside_single_image_overlay(self):
        single_source = (SOURCE_DIR / "twitter_single_image_script.js").read_text(encoding="utf-8")
        converter_source = (SOURCE_DIR / "twitter_convert_to_png.js").read_text(encoding="utf-8")
        css_source = (SOURCE_DIR / "pic_extension.css").read_text(encoding="utf-8")

        self.assertIn("downloaded-finder-png-button-container", single_source)
        self.assertIn("downloaded-finder-png-button", single_source)
        self.assertIn("parentDiv.replaceChildren(topBarDiv, contentDiv, create_png_button_container())", single_source)
        self.assertNotIn("downloaded-finder-png-button-container", converter_source)
        self.assertNotIn("document.body.appendChild(parentDiv);", converter_source)
        self.assertNotIn("bottom: 10px", css_source)

    def test_twimg_overlay_resets_browser_image_document_styles(self):
        css_source = (SOURCE_DIR / "pic_extension.css").read_text(encoding="utf-8")

        self.assertIn(".downloaded-finder-fixed img", css_source)
        self.assertIn("position: static;", css_source)
        self.assertIn("inset: auto;", css_source)
        self.assertIn("margin: 0;", css_source)
        self.assertIn("max-width: none;", css_source)
        self.assertIn("max-height: none;", css_source)


class TwitterImageExtractionTests(unittest.TestCase):
    def test_twitter_parser_lives_in_common_content_script(self):
        common_source = (SOURCE_DIR / "content_common.js").read_text(encoding="utf-8")

        self.assertIn("function parseTwitterImageName(imageUrl)", common_source)
        self.assertIn("new URL(imageUrl).pathname.split('/')", common_source)
        self.assertIn("catch", common_source)
        self.assertIn('return "";', common_source)

        for script_name in ("twitter_script.js", "twitter_single_image_script.js"):
            with self.subTest(script_name=script_name):
                source = (SOURCE_DIR / script_name).read_text(encoding="utf-8")

                self.assertNotIn("substring(28", source)
                self.assertNotIn("function parseTwitterImageName(imageUrl)", source)
                self.assertIn("parseTwitterImageName(", source)

    def test_twitter_multi_image_queries_are_guarded(self):
        source = (SOURCE_DIR / "twitter_script.js").read_text(encoding="utf-8")

        self.assertNotIn(
            "document.querySelector('div[data-testid=\"cellInnerDiv\"]').getElementsByTagName",
            source,
        )
        self.assertNotIn(
            "document.querySelector('div[data-testid=\"swipe-to-dismiss\"]').getElementsByTagName",
            source,
        )
        self.assertIn("if (!cellInnerDiv) {", source)
        self.assertIn("if (!swipeToDismiss) {", source)
        self.assertIn("if (!imgHtmlEl) {", source)
        self.assertIn("return [];", source)

    def test_twitter_scripts_skip_empty_parsed_image_names(self):
        multi_source = (SOURCE_DIR / "twitter_script.js").read_text(encoding="utf-8")
        single_source = (SOURCE_DIR / "twitter_single_image_script.js").read_text(encoding="utf-8")

        self.assertIn("let imageName = parseTwitterImageName(url);", multi_source)
        self.assertIn("if (imageName) {", multi_source)
        self.assertIn("result.push(imageName)", multi_source)

        empty_name_guard = "if (!imageInPage) {"
        self.assertIn("let imageInPage = parseTwitterImageName(currentUrl);", single_source)
        self.assertIn(empty_name_guard, single_source)
        self.assertLess(single_source.index(empty_name_guard), single_source.index("requestDownloadCheck({"))


class ReadmeDocumentationTests(unittest.TestCase):
    def test_readme_documents_cross_browser_build_and_loading(self):
        source = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("python browser_extension/build_extension.py", source)
        self.assertIn("dist/firefox", source)
        self.assertIn("dist/chrome", source)
        self.assertIn("about:debugging#/runtime/this-firefox", source)
        self.assertIn("chrome://extensions", source)
        self.assertIn("python -m uvicorn app:app --reload", source)


class SourceTreeHygieneTests(unittest.TestCase):
    def test_stale_tracked_artifacts_are_removed(self):
        stale_paths = (
            SOURCE_DIR / "manifest.json",
            REPO_ROOT / "python_server" / "test.txt",
        )

        for stale_path in stale_paths:
            with self.subTest(path=stale_path):
                self.assertFalse(stale_path.exists())

    def test_legacy_twitter_png_converter_file_is_kept(self):
        converter_path = SOURCE_DIR / "twitter_convert_to_png.js"

        self.assertTrue(converter_path.is_file())


if __name__ == "__main__":
    unittest.main()
