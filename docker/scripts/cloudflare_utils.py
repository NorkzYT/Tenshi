"""
Reusable Cloudflare template-wait utilities for Tenshi.
Place this file alongside your other scripts under `docker/scripts`.
"""

import logging
import os
import time

import cv2
import numpy as np
from PIL import ImageGrab

logger = logging.getLogger(__name__)

# Enable extra debug output if the environment flag is set
DEBUG_OPENCV = os.environ.get("DEBUG_OPENCV", "0") == "1"


def take_screenshot(debug_dir: str = "/tenshi/data/screenshots") -> np.ndarray:
    """Capture full-screen screenshot as an RGB NumPy array."""
    logger.debug("Capturing full-screen screenshot")
    screen = np.array(ImageGrab.grab())
    rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
    if DEBUG_OPENCV:
        os.makedirs(debug_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        fname = os.path.join(debug_dir, f"screenshot_{ts}.png")
        cv2.imwrite(fname, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        logger.debug("Saved debug screenshot to %s", fname)
    return rgb


def find_template_coords(
    template_path: str,
    threshold: float = 0.7,
    scales: tuple = (0.9, 1.0, 1.1),
) -> tuple[int, int] | None:
    """
    Search for a given template image on-screen.
    Returns center (x,y) if found at or above threshold, else None.
    """
    logger.debug("Loading template %s", template_path)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        logger.error("Template not found: %s", template_path)
        return None

    gray = cv2.cvtColor(take_screenshot(), cv2.COLOR_RGB2GRAY)
    best_val = 0.0
    best_loc = None
    best_size = (0, 0)

    for scale in scales:
        w = int(template.shape[1] * scale)
        h = int(template.shape[0] * scale)
        if w < 10 or h < 10:
            continue
        resized = cv2.resize(template, (w, h))
        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        logger.debug("scale %.2f → %.2f", scale, max_val)
        if max_val >= threshold and max_val > best_val:
            best_val, best_loc, best_size = max_val, max_loc, (w, h)

    if best_loc:
        x, y = best_loc
        cx = x + best_size[0] // 2
        cy = y + best_size[1] // 2
        logger.info("Template %s found at (%d,%d)", template_path, cx, cy)
        return (cx, cy)
    return None


def wait_for_template(
    template_path: str,
    threshold: float = 0.7,
    interval: float = 0.5,
    timeout: float = 30.0,
) -> tuple[int, int] | None:
    """
    Poll for the given template until it appears or timeout expires.
    Returns coords or None.
    """
    logger.info("Waiting for template %s (%.1fs timeout)...", template_path, timeout)
    end = time.time() + timeout
    while time.time() < end:
        coords = find_template_coords(template_path, threshold)
        if coords:
            return coords
        time.sleep(interval)
    logger.warning("Timeout waiting for %s", template_path)
    return None


def wait_for_page_load(
    template_path: str,
    timeout: float = 20.0,
    threshold: float = 0.75,
    interval: float = 0.5,
) -> None:
    """
    Block until Cloudflare's reload icon appears, or fallback to a fixed sleep.
    """
    logger.info("Waiting for page load via template %s", template_path)
    coords = wait_for_template(template_path, threshold, interval, timeout)
    if coords:
        logger.info("Page loaded, reload icon at %s", coords)
    else:
        logger.info("Reload button never appeared; sleeping fallback…")
        time.sleep(5)


def bypass_cf(chapter_url: str):
    try:
        logging.info("Bypassing CF for chapter %s", chapter_url)
        resp = requests.get(
            f"{FASTAPI_BASE}/trigger",
            params={"url": chapter_url, "js": "", "wait": "", "sleep": 2000},
            timeout=60,
        )
        resp.raise_for_status()
        logging.info("✅ CF bypass completed for %s", chapter_url)
    except Exception as e:
        logging.warning("CF bypass failed: %s", e)
