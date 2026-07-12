import json
import shutil
from pathlib import Path


SOURCE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SOURCE_DIR.parent
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "dist"

BROWSER_MANIFESTS = {
    "chrome": "manifest.chrome.json",
    "firefox": "manifest.firefox.json",
}

SHARED_FILE_SUFFIXES = {".css", ".html", ".js"}
EXCLUDED_FILENAMES = {
    "build_extension.py",
    "manifest.json",
    "manifest.chrome.json",
    "manifest.firefox.json",
    "test_extension_build.py",
    "test_extension_static.py",
}


def copy_shared_assets(target_dir: Path) -> None:
    for source_file in SOURCE_DIR.iterdir():
        if source_file.name in EXCLUDED_FILENAMES:
            continue
        if source_file.is_file() and source_file.suffix in SHARED_FILE_SUFFIXES:
            shutil.copy2(source_file, target_dir / source_file.name)

    images_dir = SOURCE_DIR / "images"
    if not images_dir.is_dir():
        raise FileNotFoundError(f"Missing required images directory: {images_dir}")
    shutil.copytree(images_dir, target_dir / "images")


def write_manifest(browser: str, target_dir: Path) -> None:
    manifest_name = BROWSER_MANIFESTS[browser]
    manifest_path = SOURCE_DIR / manifest_name
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing manifest template: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    (target_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=4) + "\n",
        encoding="utf-8",
    )


def build_browser(browser: str, output_root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    if browser not in BROWSER_MANIFESTS:
        raise ValueError(f"Unsupported browser: {browser}")

    target_dir = Path(output_root) / browser
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True)

    copy_shared_assets(target_dir)
    write_manifest(browser, target_dir)
    return target_dir


def build_all(output_root: Path = DEFAULT_OUTPUT_ROOT) -> list[Path]:
    return [build_browser(browser, Path(output_root)) for browser in BROWSER_MANIFESTS]


def main() -> None:
    build_all(DEFAULT_OUTPUT_ROOT)
    print(f"Built extension outputs in {DEFAULT_OUTPUT_ROOT}")


if __name__ == "__main__":
    main()
