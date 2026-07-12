# 05_chrome_download_checker

Browser extension and local Python backend for checking whether images from supported websites already exist in configured local folders.

## Components

- `browser_extension/`: shared WebExtension source for Chrome and Firefox.
- `python_server/`: FastAPI backend that scans configured folders and exposes lookup endpoints.

## Build Browser Extensions

Run from the repository root:

```bash
python browser_extension/build_extension.py
```

The build creates these generated directories:

- `dist/chrome`: load this in Chrome.
- `dist/firefox`: load this in Firefox.

## Run The Backend

Install the Python dependencies, then start the backend from `python_server/`:

```bash
python -m uvicorn app:app --reload
```

The extension expects the backend at `http://localhost:8000` by default.

## Load In Firefox

1. Open `about:debugging#/runtime/this-firefox`.
2. Click `Load Temporary Add-on`.
3. Select `dist/firefox/manifest.json`.

## Load In Chrome

1. Open `chrome://extensions`.
2. Enable `Developer mode`.
3. Click `Load unpacked`.
4. Select `dist/chrome`.

## Supported Pages

- `https://www.pixiv.net/en/artworks/*`
- `https://twitter.com/*/status/*`
- `https://pbs.twimg.com/*`
