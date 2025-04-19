import logging
import os
import sys
import time
from urllib.parse import urlparse

import requests
from playwright.sync_api import sync_playwright
from scripts.cloudflare_utils import bypass_cf
from scripts.utils import CDP_ENDPOINT, FASTAPI_BASE


def scroll_to_bottom(page, repeats=5, delay=0.3):
    """Press End key `repeats` times with a short delay to trigger lazy‑load."""
    for _ in range(repeats):
        page.keyboard.press("End")
        time.sleep(delay)


def extract_chapter_folder(chapter_url: str) -> str:
    for seg in urlparse(chapter_url).path.rstrip("/").split("/"):
        if seg.lower().startswith("chapter"):
            return seg
    return "default_chapter"


def save_image(chapter_url: str, image_url: str):
    chapter = extract_chapter_folder(chapter_url)
    target_dir = os.path.join("/tenshi/data", chapter)
    os.makedirs(target_dir, exist_ok=True)
    filename = os.path.basename(urlparse(image_url).path)
    out_path = os.path.join(target_dir, filename)

    bypass_cf(chapter_url)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(CDP_ENDPOINT)
        context = browser.contexts[0]
        page = context.new_page()

        # 1) Load chapter page so cookies are shared
        page.goto(chapter_url, wait_until="networkidle")
        logging.info("Loaded chapter page, now scrolling to load all images…")

        # 2) Scroll to the bottom a few times to trigger lazy‑load
        scroll_to_bottom(page)

        # 3) Now fetch the image URL
        logging.info("Fetching image %s", filename)
        response = page.goto(image_url, wait_until="networkidle")
        if not response or response.status != 200:
            raise RuntimeError(
                f"Failed to load {image_url}: {response.status if response else 'no response'}"
            )
        img_bytes = response.body()

        # 4) Write out to disk
        with open(out_path, "wb") as f:
            f.write(img_bytes)
        logging.info("✔ Saved %s", out_path)

        page.close()
        browser.close()


def main():
    if len(sys.argv) != 3:
        print("Usage: save_image_automation.py <chapter_url> <image_url>")
        sys.exit(1)

    chapter_url, image_url = sys.argv[1], sys.argv[2]
    try:
        save_image(chapter_url, image_url)
    except Exception as e:
        logging.error("Error saving %s: %s", image_url, e)
        sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    main()
