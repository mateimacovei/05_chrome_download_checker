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

function normalize(value) {
  return JSON.parse(JSON.stringify(value));
}

function loadCommon(options = {}) {
  const sendMessages = [];
  let lastError = options.initialLastError || null;
  const context = {
    URL,
    chrome: {
      runtime: {
        get lastError() {
          return lastError;
        },
        sendMessage(message, callback) {
          sendMessages.push(normalize(message));
          if (options.lastErrorBeforeCallback) {
            lastError = { message: "runtime failure" };
          }
          if (callback) {
            callback(options.response);
          }
        },
      },
    },
  };

  vm.createContext(context);
  vm.runInContext(fs.readFileSync(contentCommonPath, "utf8"), context, {
    filename: contentCommonPath,
  });

  return { helpers: context.downloadedFinderExtension, sendMessages };
}

async function requestDownloadCheckSendsCheckDownloadsAndReturnsData() {
  const data = [{ name: "found", path: "/tmp/found.jpg" }];
  const { helpers, sendMessages } = loadCommon({ response: { ok: true, data } });
  let callbackData = undefined;

  helpers.requestDownloadCheck({
    method: "GET",
    path: "/contains",
    query: { name: "pixiv image" },
  }, (responseData) => {
    callbackData = normalize(responseData);
  });

  assert.deepEqual(sendMessages, [{
    type: "CHECK_DOWNLOADS",
    method: "GET",
    path: "/contains",
    query: { name: "pixiv image" },
  }]);
  assert.deepEqual(callbackData, data);
}

async function requestDownloadCheckReturnsNullOnFailure() {
  const cases = [
    { response: { ok: false } },
    { response: null },
    { response: { ok: true, data: [] }, lastErrorBeforeCallback: true },
  ];

  for (const options of cases) {
    const { helpers } = loadCommon(options);
    let callbackData = undefined;

    helpers.requestDownloadCheck({ method: "POST", path: "/contains", body: ["image"] }, (data) => {
      callbackData = data;
    });

    assert.equal(callbackData, null);
  }
}

async function parseTwitterImageNameUsesSafeUrlPathStemExtraction() {
  const { helpers } = loadCommon();

  assert.equal(
    helpers.parseTwitterImageName("https://pbs.twimg.com/media/AbCdEf.jpg?format=jpg"),
    "AbCdEf",
  );
  assert.equal(
    helpers.parseTwitterImageName("https://pbs.twimg.com/media/AbCdEf?format=jpg&name=large"),
    "AbCdEf",
  );
  assert.equal(helpers.parseTwitterImageName("not a valid url"), "");
  assert.equal(helpers.parseTwitterImageName(""), "");
}

const tests = {
  requestDownloadCheckSendsCheckDownloadsAndReturnsData,
  requestDownloadCheckReturnsNullOnFailure,
  parseTwitterImageNameUsesSafeUrlPathStemExtraction,
};

if (!tests[testName]) {
  throw new Error(`Unknown test: ${testName}`);
}

tests[testName]().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
"""


class ContentCommonBehaviorTests(unittest.TestCase):
    maxDiff = None

    def run_node_case(self, test_name):
        env = os.environ.copy()
        env["CONTENT_COMMON_JS_PATH"] = str(SOURCE_DIR / "content_common.js")
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
                Node content_common.js behavior case failed: {test_name}
                stdout:
                {result.stdout}
                stderr:
                {result.stderr}
                """
            ).strip(),
        )

    def test_request_download_check_sends_check_downloads_and_returns_data(self):
        self.run_node_case("requestDownloadCheckSendsCheckDownloadsAndReturnsData")

    def test_request_download_check_returns_null_on_failure(self):
        self.run_node_case("requestDownloadCheckReturnsNullOnFailure")

    def test_parse_twitter_image_name_uses_safe_url_path_stem_extraction(self):
        self.run_node_case("parseTwitterImageNameUsesSafeUrlPathStemExtraction")


if __name__ == "__main__":
    unittest.main()
