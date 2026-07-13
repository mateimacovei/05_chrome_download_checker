import os
import subprocess
import textwrap
import unittest
from pathlib import Path


SOURCE_DIR = Path(__file__).resolve().parent


NODE_HARNESS = r"""
const assert = require("assert/strict");
const fs = require("fs");
const vm = require("vm");

const testName = process.argv[1];
const contentCommonPath = process.env.CONTENT_COMMON_JS_PATH;
const twitterPath = process.env.TWITTER_JS_PATH;
const twitterSingleImagePath = process.env.TWITTER_SINGLE_IMAGE_JS_PATH;

function normalize(value) {
  return JSON.parse(JSON.stringify(value));
}

function textFromChildren(children) {
  return children.map((child) => child.textContent || "").join("");
}

function createElement(tagName, options = {}) {
  return {
    tagName,
    alt: options.alt || "",
    children: [],
    classList: { add() {} },
    draggable: false,
    images: options.images || [],
    src: options.src || "",
    style: {},
    textContent: options.textContent || "",
    title: "",
    addEventListener() {},
    appendChild(child) {
      this.children.push(child);
      this.textContent = textFromChildren(this.children);
    },
    getAttribute(attributeName) {
      if (attributeName === "alt") {
        return this.alt;
      }
      if (attributeName === "src") {
        return this.src;
      }
      return this[attributeName] || null;
    },
    getElementsByTagName(tag) {
      if (tag === "img") {
        return this.images;
      }
      return [];
    },
    replaceChildren(...children) {
      this.children = children;
      this.textContent = textFromChildren(children);
    },
  };
}

function createDocument(options = {}) {
  const contentTexts = [];
  const body = createElement("body");

  return {
    body,
    contentTexts,
    title: "Twitter",
    createElement(tagName) {
      const element = createElement(tagName);
      const originalReplaceChildren = element.replaceChildren.bind(element);
      element.replaceChildren = (...children) => {
        originalReplaceChildren(...children);
        if (element.textContent) {
          contentTexts.push(element.textContent);
        }
      };
      return element;
    },
    createTextNode(text) {
      return { textContent: text };
    },
    querySelector(selector) {
      return (options.querySelector && options.querySelector[selector]) || null;
    },
    querySelectorAll(selector) {
      return (options.querySelectorAll && options.querySelectorAll[selector]) || [];
    },
  };
}

function loadScript(scriptPath, options) {
  const sendMessages = [];
  const document = createDocument(options.document || {});
  const context = {
    URL,
    chrome: {
      runtime: {
        lastError: null,
        getURL(path) {
          return `chrome-extension://${path}`;
        },
        sendMessage(message, callback) {
          sendMessages.push(normalize(message));
          if (callback) {
            callback({ ok: true, data: [] });
          }
        },
      },
      storage: {
        sync: {
          get(keys, callback) {
            if (keys === "color") {
              callback({ color: "rgb(0 0 0)" });
              return;
            }
            callback({ hidden: false });
          },
          set() {},
        },
      },
    },
    console: { log() {} },
    document,
    setTimeout(callback) {
      callback();
      return 0;
    },
    window: { location: { href: options.href } },
  };

  vm.createContext(context);
  vm.runInContext(fs.readFileSync(contentCommonPath, "utf8"), context, { filename: contentCommonPath });
  vm.runInContext(fs.readFileSync(scriptPath, "utf8"), context, { filename: scriptPath });

  return { document, sendMessages };
}

function image(src, alt = "Image") {
  return createElement("img", { alt, src });
}

function imageContainer(images) {
  return createElement("div", { images });
}

function loadSingleImageScript(href) {
  return loadScript(twitterSingleImagePath, { href });
}

function loadTwitterScriptForCellImages(href, images) {
  return loadScript(twitterPath, {
    href,
    document: {
      querySelector: {
        'div[data-testid="cellInnerDiv"]': imageContainer(images),
      },
    },
  });
}

function assertNoImageMessage(document) {
  assert.equal(
    document.contentTexts.includes("No image found. Go to tweet"),
    true,
    `Expected no-image message in ${JSON.stringify(document.contentTexts)}`,
  );
}

async function singleImageSendsParsedPbsImageName() {
  const { sendMessages } = loadSingleImageScript(
    "https://pbs.twimg.com/media/AbCdEf?format=jpg&name=large",
  );

  assert.deepEqual(sendMessages, [{
    type: "CHECK_DOWNLOADS",
    method: "GET",
    path: "/contains",
    query: { name: "AbCdEf" },
  }]);
}

async function singleImageStripsExtensionFromPbsImageName() {
  const { sendMessages } = loadSingleImageScript(
    "https://pbs.twimg.com/media/AbCdEf.jpg?format=jpg",
  );

  assert.equal(sendMessages.length, 1);
  assert.deepEqual(sendMessages[0].query, { name: "AbCdEf" });
}

async function singleImageInvalidUrlDoesNotSendBackendRequest() {
  const { document, sendMessages } = loadSingleImageScript("not a valid url");

  assert.deepEqual(sendMessages, []);
  assertNoImageMessage(document);
}

async function singleImageMissingImageNameDoesNotSendBackendRequest() {
  const { document, sendMessages } = loadSingleImageScript(
    "https://pbs.twimg.com/media/?format=jpg",
  );

  assert.deepEqual(sendMessages, []);
  assertNoImageMessage(document);
}

async function multiImageInvalidExtractedSrcShowsNoImageWithoutBackendRequest() {
  const { document, sendMessages } = loadTwitterScriptForCellImages(
    "https://twitter.com/user/status/123",
    [image("not a valid url")],
  );

  assert.deepEqual(sendMessages, []);
  assertNoImageMessage(document);
}

async function multiImageExtractFromImagesStripsExtension() {
  const { sendMessages } = loadTwitterScriptForCellImages(
    "https://twitter.com/user/status/123",
    [image("https://pbs.twimg.com/media/AbCdEf.jpg?format=jpg")],
  );

  assert.equal(sendMessages.length, 1);
  assert.deepEqual(sendMessages[0].body, ["AbCdEf"]);
}

const tests = {
  singleImageSendsParsedPbsImageName,
  singleImageStripsExtensionFromPbsImageName,
  singleImageInvalidUrlDoesNotSendBackendRequest,
  singleImageMissingImageNameDoesNotSendBackendRequest,
  multiImageInvalidExtractedSrcShowsNoImageWithoutBackendRequest,
  multiImageExtractFromImagesStripsExtension,
};

if (!tests[testName]) {
  throw new Error(`Unknown test: ${testName}`);
}

tests[testName]().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
"""


class TwitterContentScriptBehaviorTests(unittest.TestCase):
    maxDiff = None

    def run_node_case(self, test_name):
        env = os.environ.copy()
        env["CONTENT_COMMON_JS_PATH"] = str(SOURCE_DIR / "content_common.js")
        env["TWITTER_JS_PATH"] = str(SOURCE_DIR / "twitter_script.js")
        env["TWITTER_SINGLE_IMAGE_JS_PATH"] = str(SOURCE_DIR / "twitter_single_image_script.js")
        result = subprocess.run(
            ["node", "-e", NODE_HARNESS, test_name],
            cwd=SOURCE_DIR,
            env=env,
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=textwrap.dedent(
                f"""
                Node Twitter content script behavior case failed: {test_name}
                stdout:
                {result.stdout}
                stderr:
                {result.stderr}
                """
            ).strip(),
        )

    def test_single_image_sends_parsed_pbs_image_name(self):
        self.run_node_case("singleImageSendsParsedPbsImageName")

    def test_single_image_strips_extension_from_pbs_image_name(self):
        self.run_node_case("singleImageStripsExtensionFromPbsImageName")

    def test_single_image_invalid_url_does_not_send_backend_request(self):
        self.run_node_case("singleImageInvalidUrlDoesNotSendBackendRequest")

    def test_single_image_missing_image_name_does_not_send_backend_request(self):
        self.run_node_case("singleImageMissingImageNameDoesNotSendBackendRequest")

    def test_multi_image_invalid_extracted_src_shows_no_image_without_backend_request(self):
        self.run_node_case("multiImageInvalidExtractedSrcShowsNoImageWithoutBackendRequest")

    def test_multi_image_extract_from_images_strips_extension(self):
        self.run_node_case("multiImageExtractFromImagesStripsExtension")


if __name__ == "__main__":
    unittest.main()
