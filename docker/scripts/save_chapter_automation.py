#!/usr/bin/env python3
import json
import logging
import os
import sys
import time
from http import cookiejar
from urllib.parse import unquote, urlparse

import requests
from playwright.sync_api import sync_playwright
from scripts.cloudflare_utils import bypass_cf
from scripts.utils import CDP_ENDPOINT, FASTAPI_BASE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scroll_to_bottom(page, repeats=10, delay=0.2):
    for _ in range(repeats):
        page.keyboard.press("End")
        time.sleep(delay)


def extract_folder(chapter_url: str) -> str:
    return unquote(urlparse(chapter_url).path.rstrip("/").split("/")[-1])


def save_chapter(chapter_url: str, js: str, slug: str):
    folder = unquote(urlparse(chapter_url).path.rstrip("/").split("/")[-1])
    out_dir = os.path.join("/tenshi/data", slug, folder)
    os.makedirs(out_dir, exist_ok=True)

    # 1) Bypass CF
    bypass_cf(chapter_url)

    with sync_playwright() as pw:
        # 2) Connect to the existing browser and create a new page
        browser = pw.chromium.connect_over_cdp(CDP_ENDPOINT)
        context = browser.contexts[0]
        page = context.new_page()

        # 3) Harvest cookies into a requests session
        cj = cookiejar.CookieJar()
        for c in context.cookies():
            cj.set_cookie(
                cookiejar.Cookie(
                    version=0,
                    name=c["name"],
                    value=c["value"],
                    port=None,
                    port_specified=False,
                    domain=c["domain"],
                    domain_specified=True,
                    domain_initial_dot=False,
                    path=c["path"],
                    path_specified=True,
                    secure=c["secure"],
                    expires=None,
                    discard=True,
                    comment=None,
                    comment_url=None,
                    rest={},
                    rfc2109=False,
                )
            )
        session = requests.Session()
        session.cookies = cj
        session.headers.update({"Referer": chapter_url})

        # 4) Load chapter & scroll to force lazy‐load
        page.goto(chapter_url, wait_until="networkidle")
        logger.info("Loaded %s – scrolling to force lazy‑load", chapter_url)
        scroll_to_bottom(page, repeats=20, delay=0.1)

        # 5) Grab all image URLs by running the provided JS
        logger.info("Extracting image URLs via JS")
        raw = page.evaluate(js)
        try:
            srcs = json.loads(raw)
        except Exception:
            logger.error("Failed to parse JSON from JS result: %s", raw)
            srcs = []
        logger.info("Found %d images", len(srcs))

        # inside your save_chapter_automation.py, after you harvest cookies into `context`:
        api_request = context.request  # this is a built‑in Playwright API for HTTP
        for src in srcs:
            fname = os.path.basename(urlparse(src).path)
            out_path = os.path.join(out_dir, fname)
            if os.path.exists(out_path):
                continue

            logger.info("Downloading %s via Playwright APIRequest", fname)
            try:
                resp = api_request.get(src, headers={"Referer": chapter_url})
                if resp.status != 200:
                    logger.error("Failed to fetch %s: status %d", src, resp.status)
                    continue
                body = resp.body()
            except Exception as e:
                logger.error("Playwright request for %s threw: %s", src, e)
                continue

            with open(out_path, "wb") as f:
                f.write(body)

        page.close()
        browser.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: save_chapter_automation.py <chapter_url> <js_snippet> <slug>")
        sys.exit(1)

    chapter_url = sys.argv[1]
    js = sys.argv[2]
    slug = sys.argv[3]
    save_chapter(chapter_url, js, slug)
