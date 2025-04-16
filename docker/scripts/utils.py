#!/usr/bin/env python3
"""
Tenshi utilities: screenshot capture, template matching, and wait routines.
"""
import os
import time
import logging
import cv2
import numpy as np
from PIL import ImageGrab

logger = logging.getLogger(__name__)
DEBUG_OPENCV = os.environ.get("DEBUG_OPENCV", "0") == "1"


def take_screenshot(debug_dir="/tenshi/data/screenshots"):
    """Capture full-screen screenshot as RGB array."""
    logger.debug("Capturing screenshot")
    screen = np.array(ImageGrab.grab())
    rgb = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
    if DEBUG_OPENCV:
        os.makedirs(debug_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        fname = os.path.join(debug_dir, f"screenshot_{ts}.png")
        cv2.imwrite(fname, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
        logger.debug("Saved debug screenshot to %s", fname)
    return rgb


def find_template_coords(template_path, threshold=0.7, scales=(0.9, 1.0, 1.1)):
    """Search for template on screen; return center coords if found else None."""
    logger.debug("Loading template %s", template_path)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        logger.error("Template not found: %s", template_path)
        return None

    gray = cv2.cvtColor(take_screenshot(), cv2.COLOR_RGB2GRAY)
    best = {"val": 0, "loc": None, "size": None}

    for scale in scales:
        w, h = int(template.shape[1] * scale), int(template.shape[0] * scale)
        if w < 10 or h < 10:
            continue
        resized = cv2.resize(template, (w, h))
        result = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        logger.debug("scale %.2f → %.2f", scale, max_val)
        if max_val >= threshold and max_val > best["val"]:
            best.update(val=max_val, loc=max_loc, size=(w, h))

    if best["loc"]:
        x, y = best["loc"]
        cx = x + best["size"][0] // 2
        cy = y + best["size"][1] // 2
        logger.info("Template %s found at (%d,%d)", template_path, cx, cy)
        return (cx, cy)
    return None


def wait_for_template(template_path, threshold=0.7, interval=0.5, timeout=30.0):
    """Poll until template appears or timeout. Returns coords or None."""
    logger.info("Waiting for template %s (%.1fs timeout)...", template_path, timeout)
    end = time.time() + timeout
    while time.time() < end:
        coords = find_template_coords(template_path, threshold)
        if coords:
            return coords
        time.sleep(interval)
    logger.warning("Timeout waiting for %s", template_path)
    return None
