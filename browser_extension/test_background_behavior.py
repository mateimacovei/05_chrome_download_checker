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
const backgroundPath = process.env.BACKGROUND_JS_PATH;

function loadBackground(options) {
  const fetchCalls = [];
  let messageListener = null;
  const backendUrl = options.backendUrl || "http://backend.test";

  function normalize(value) {
    return JSON.parse(JSON.stringify(value));
  }

  const context = {
    URLSearchParams,
    console: { log() {} },
    fetch(url, fetchOptions) {
      fetchCalls.push(normalize({ url, fetchOptions }));
      if (options.fetchRejects) {
        return Promise.reject(new Error("network failure"));
      }
      return Promise.resolve(options.response || {
        ok: true,
        json: async () => options.jsonData,
      });
    },
    chrome: {
      runtime: {
        onInstalled: { addListener() {} },
        onMessage: {
          addListener(listener) {
            messageListener = listener;
          },
        },
      },
      storage: {
        sync: {
          set() {},
          get(keys, callback) {
            assert.equal(Array.isArray(keys), true);
            assert.equal(keys.length, 1);
            assert.equal(keys[0], "backendUrl");
            callback({ backendUrl });
          },
        },
      },
      tabs: { query() {}, update() {} },
    },
  };

  vm.createContext(context);
  vm.runInContext(fs.readFileSync(backgroundPath, "utf8"), context, { filename: backgroundPath });
  assert.equal(typeof messageListener, "function");

  return { fetchCalls, messageListener };
}

async function dispatchMessage(messageListener, request) {
  const responses = [];
  let returned;
  const responsePromise = new Promise((resolve) => {
    returned = messageListener(
      request,
      { tab: { url: "https://content.example/page" } },
      (response) => {
        const normalizedResponse = JSON.parse(JSON.stringify(response));
        responses.push(normalizedResponse);
        resolve(normalizedResponse);
      },
    );
  });

  const response = await Promise.race([
    responsePromise,
    new Promise((resolve, reject) => {
      setTimeout(() => reject(new Error("sendResponse was not called")), 100);
    }),
  ]);

  return { returned, response, responses };
}

async function checkDownloadsGetBuildsEncodedQueryAndReturnsJson() {
  const data = [{ name: "found", path: "/tmp/found.jpg" }];
  const { fetchCalls, messageListener } = loadBackground({
    backendUrl: "http://localhost:8123",
    jsonData: data,
  });

  const result = await dispatchMessage(messageListener, {
    type: "CHECK_DOWNLOADS",
    method: "GET",
    path: "/contains",
    query: { name: "pixiv image&1" },
  });

  assert.equal(result.returned, true);
  assert.deepEqual(result.response, { ok: true, data });
  assert.equal(result.responses.length, 1);
  assert.equal(fetchCalls.length, 1);
  assert.equal(fetchCalls[0].url, "http://localhost:8123/contains?name=pixiv+image%261");
  assert.deepEqual(fetchCalls[0].fetchOptions, { method: "GET" });
}

async function checkDownloadsPostSendsJsonBodyAndReturnsJson() {
  const data = [{ name: "saved" }];
  const body = ["image-one", "image-two"];
  const { fetchCalls, messageListener } = loadBackground({
    backendUrl: "http://localhost:8123",
    jsonData: data,
  });

  const result = await dispatchMessage(messageListener, {
    type: "CHECK_DOWNLOADS",
    method: "POST",
    path: "/contains",
    body,
  });

  assert.equal(result.returned, true);
  assert.deepEqual(result.response, { ok: true, data });
  assert.equal(result.responses.length, 1);
  assert.equal(fetchCalls.length, 1);
  assert.equal(fetchCalls[0].url, "http://localhost:8123/contains");
  assert.equal(fetchCalls[0].fetchOptions.method, "POST");
  assert.deepEqual(fetchCalls[0].fetchOptions.headers, {
    "Content-Type": "application/json;charset=UTF-8",
  });
  assert.equal(fetchCalls[0].fetchOptions.body, JSON.stringify(body));
}

async function checkDownloadsNonOkResponseSendsFailure() {
  const { fetchCalls, messageListener } = loadBackground({
    backendUrl: "http://localhost:8123",
    response: {
      ok: false,
      json: async () => {
        throw new Error("json should not be read for non-ok responses");
      },
    },
  });

  const result = await dispatchMessage(messageListener, {
    type: "CHECK_DOWNLOADS",
    method: "GET",
    path: "/contains",
    query: { name: "missing" },
  });

  assert.equal(result.returned, true);
  assert.deepEqual(result.response, { ok: false });
  assert.equal(result.responses.length, 1);
  assert.equal(fetchCalls.length, 1);
}

async function checkDownloadsRejectedFetchSendsFailure() {
  const { fetchCalls, messageListener } = loadBackground({
    backendUrl: "http://localhost:8123",
    fetchRejects: true,
  });

  const result = await dispatchMessage(messageListener, {
    type: "CHECK_DOWNLOADS",
    method: "POST",
    path: "/contains",
    body: ["image-one"],
  });

  assert.equal(result.returned, true);
  assert.deepEqual(result.response, { ok: false });
  assert.equal(result.responses.length, 1);
  assert.equal(fetchCalls.length, 1);
}

const tests = {
  checkDownloadsGetBuildsEncodedQueryAndReturnsJson,
  checkDownloadsPostSendsJsonBodyAndReturnsJson,
  checkDownloadsNonOkResponseSendsFailure,
  checkDownloadsRejectedFetchSendsFailure,
};

if (!tests[testName]) {
  throw new Error(`Unknown test: ${testName}`);
}

tests[testName]().catch((error) => {
  console.error(error && error.stack ? error.stack : error);
  process.exitCode = 1;
});
"""


class BackgroundMessageBehaviorTests(unittest.TestCase):
    maxDiff = None

    def run_node_case(self, test_name):
        env = os.environ.copy()
        env["BACKGROUND_JS_PATH"] = str(SOURCE_DIR / "background.js")
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
                Node background.js behavior case failed: {test_name}
                stdout:
                {result.stdout}
                stderr:
                {result.stderr}
                """
            ).strip(),
        )

    def test_check_downloads_get_builds_encoded_query_and_returns_json(self):
        self.run_node_case("checkDownloadsGetBuildsEncodedQueryAndReturnsJson")

    def test_check_downloads_post_sends_json_body_and_returns_json(self):
        self.run_node_case("checkDownloadsPostSendsJsonBodyAndReturnsJson")

    def test_check_downloads_non_ok_response_sends_failure(self):
        self.run_node_case("checkDownloadsNonOkResponseSendsFailure")

    def test_check_downloads_rejected_fetch_sends_failure(self):
        self.run_node_case("checkDownloadsRejectedFetchSendsFailure")


if __name__ == "__main__":
    unittest.main()
