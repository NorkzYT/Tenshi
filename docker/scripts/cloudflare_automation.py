#!/usr/bin/env python3
"""
Cloudflare automation: wait for reload-button, simulate challenge click.
"""
import logging
import subprocess
import time

from scripts.utils import find_template_coords, wait_for_page_load, wait_for_template

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CHALLENGE_TPL = "/tenshi/images/cloudflare_verify_click_template_light.png"


def simulate_click(x, y):
    subprocess.check_call(
        ["xdotool", "mousemove", "--sync", str(x), str(y), "click", "1"]
    )


def main():
    wait_for_page_load()

    # detect & click Cloudflare challenge if present
    coords = wait_for_template(
        CHALLENGE_TPL,
        threshold=0.7,
        interval=0.5,
        timeout=10.0,
    )
    if coords:
        logger.info("Clicking Cloudflare challenge at %s", coords)
        simulate_click(*coords)
        time.sleep(1)
    else:
        logger.info("No challenge template detected; skipping.")


if __name__ == "__main__":
    main()
