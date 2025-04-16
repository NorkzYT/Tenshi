#!/usr/bin/env python3
"""
Cloudflare automation: wait for reload-button, simulate challenge click.
"""
import logging
import time
import subprocess
from scripts.utils import wait_for_template, find_template_coords

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RELOAD_TPL = "/tenshi/images/reload-button-template.png"
CHALLENGE_TPL = "/tenshi/images/cloudflare_verify_click_template_light.png"


def simulate_click(x, y):
    subprocess.check_call(
        ["xdotool", "mousemove", "--sync", str(x), str(y), "click", "1"]
    )


def main():
    # wait for page to finish loading (reload icon)
    coords = wait_for_template(RELOAD_TPL, threshold=0.75, interval=0.5, timeout=20)
    if not coords:
        logger.info("Reload button never appeared; sleeping fallback…")
        time.sleep(5)
    else:
        logger.info("Page loaded, reload icon at %s", coords)

    # detect & click Cloudflare challenge if present
    coords = find_template_coords(CHALLENGE_TPL, threshold=0.7)
    if coords:
        logger.info("Clicking Cloudflare challenge at %s", coords)
        simulate_click(*coords)
        time.sleep(15)
    else:
        logger.info("No challenge template detected; skipping.")


if __name__ == "__main__":
    main()
