#!/usr/bin/env python3
"""
Cloudflare automation: wait for reload-button, simulate challenge click.
Runs bypass only if Cloudflare logo is detected to save time when no challenge is present.
"""
import logging
import subprocess
import time

from scripts.cloudflare_utils import (
    find_template_coords,
    wait_for_page_load,
    wait_for_template,
)
from scripts.utils import RELOAD_TPL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to the Cloudflare logo and challenge templates
LOGO_TPL = "/tenshi/images/cloudflare_logo_template.png"
CHALLENGE_TPL = "/tenshi/images/cloudflare_verify_click_template_light.png"


def simulate_click(x, y):
    """
    Move mouse to (x, y) and perform a click using xdotool.
    """
    subprocess.check_call(
        ["xdotool", "mousemove", "--sync", str(x), str(y), "click", "1"]
    )


def main():
    # 1) Wait for the page to load (detect reload icon or fallback sleep)
    wait_for_page_load(template_path=RELOAD_TPL)

    # 2) Early detection: check for Cloudflare logo presence
    # Use broader scales and lower threshold to improve detection
    logo_coords = find_template_coords(
        LOGO_TPL, threshold=0.2, scales=(0.5, 0.75, 1.0, 1.25)
    )
    if not logo_coords:
        logger.info("No Cloudflare logo detected; skipping challenge bypass.")
        return

    logger.info(
        "Cloudflare logo detected at %s; proceeding with challenge bypass.", logo_coords
    )

    # 3) detect & click Cloudflare challenge if present
    coords = wait_for_template(
        CHALLENGE_TPL,
        threshold=0.75,
        interval=0.5,
        timeout=10.0,
    )
    if coords:
        logger.info("Clicking Cloudflare challenge at %s", coords)
        simulate_click(*coords)
        time.sleep(1)
    else:
        logger.info("Challenge template not detected; nothing to click.")


if __name__ == "__main__":
    main()
