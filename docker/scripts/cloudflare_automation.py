#!/usr/bin/env python3
"""
Cloudflare Automation Script (with debugging)

Steps:
1. Wait for the page to fully load.
2. Optionally check for a "Verifying…" spinner template.
3. Check for the main Cloudflare challenge template (cloudflare_verify_click_template_light.png)
   and, if found, simulate a click.
4. Wait for any redirect to finish.
5. Poll for cookies from Brave until available, then save them to /cloudflareopencv/data/cloudflare_cookies.json.
6. When DEBUG_OPENCV is set, intermediate screenshots are saved.
"""

import cv2
import numpy as np
import subprocess
import time
import logging
import json
from PIL import ImageGrab
import browser_cookie3
import os

# Configure logging.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

if os.environ.get("DEBUG_OPENCV", "0") == "1":
    logging.info("DEBUG_OPENCV is enabled: Saving screenshots for debugging.")


def take_screenshot(debug_dir="/cloudflareopencv/data/screenshots"):
    """Capture a screenshot and save it if debugging is enabled."""
    logging.info("Taking a screenshot of the current screen...")
    screen = np.array(ImageGrab.grab())
    rgb_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2RGB)
    if os.environ.get("DEBUG_OPENCV", "0") == "1":
        try:
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir, exist_ok=True)
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            debug_filename = os.path.join(debug_dir, f"screenshot_{timestamp}.png")
            cv2.imwrite(debug_filename, cv2.cvtColor(rgb_screen, cv2.COLOR_RGB2BGR))
            logging.info("Saved screenshot to %s", debug_filename)
        except Exception as ex:
            logging.error("Failed to save screenshot: %s", ex)
    return rgb_screen


def find_template_coords(template_path, threshold=0.7, scales=[0.9, 1.0, 1.1]):
    """
    Search for the provided template image using multi-scale matching.
    Returns (center_x, center_y) if found, otherwise None.
    """
    logging.info("Loading template image from: %s", template_path)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if template is None:
        logging.error("Could not load template image from %s", template_path)
        return None

    screenshot = take_screenshot()
    gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

    best_match_val = 0
    best_match_loc = None
    best_template_size = None

    for scale in scales:
        new_w = int(template.shape[1] * scale)
        new_h = int(template.shape[0] * scale)
        if new_w < 10 or new_h < 10:
            continue
        resized_template = cv2.resize(template, (new_w, new_h))
        result = cv2.matchTemplate(gray_screen, resized_template, cv2.TM_CCOEFF_NORMED)
        _, maxVal, _, maxLoc = cv2.minMaxLoc(result)
        logging.info("Scale %.2f – max correlation value: %.2f", scale, maxVal)
        if maxVal > best_match_val and maxVal >= threshold:
            best_match_val = maxVal
            best_match_loc = maxLoc
            best_template_size = (new_w, new_h)

    if best_match_loc is not None:
        top_left = best_match_loc
        w, h = best_template_size
        center_x = top_left[0] + w // 2
        center_y = top_left[1] + h // 2
        logging.info(
            "Template found (score=%.2f) at (%d, %d)",
            best_match_val,
            center_x,
            center_y,
        )
        return (center_x, center_y)
    else:
        logging.info("Template not found at any scale.")
        return None


def wait_until_template_disappears(
    template_path, threshold=0.7, check_interval=2, timeout=20
):
    """
    Poll until the template disappears or the timeout is reached.
    """
    logging.info(
        "Waiting until template %s disappears (timeout=%s seconds)...",
        template_path,
        timeout,
    )
    start_time = time.time()
    while True:
        coords = find_template_coords(template_path, threshold=threshold)
        if coords is not None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                logging.info(
                    "Template is still present after %d seconds. Giving up.", timeout
                )
                return False
            logging.info("Template still found. Sleeping %d seconds...", check_interval)
            time.sleep(check_interval)
        else:
            logging.info("Template disappeared. Proceeding.")
            return True


def simulate_click(x, y):
    """Simulate a mouse click using xdotool."""
    logging.info("Simulating mouse click at (%d, %d)...", x, y)
    try:
        subprocess.check_call(
            ["xdotool", "mousemove", "--sync", str(x), str(y), "click", "1"]
        )
        logging.info("Mouse click executed successfully.")
    except subprocess.CalledProcessError as e:
        logging.error("Error while executing xdotool command: %s", e)


def serialize_cookie(cookie):
    """
    Convert a cookie object to a serializable dictionary.
    """
    return {
        "domain": cookie.domain,
        "name": cookie.name,
        "value": cookie.value,
        "path": cookie.path,
        "expires": cookie.expires,
        "secure": cookie.secure,
        "httpOnly": bool(cookie.has_nonstandard_attr("HttpOnly")),
    }


def poll_for_cookies(timeout=60, interval=3):
    """
    Poll for cookies from Brave for up to 'timeout' seconds.

    Returns:
        A list of cookie objects if found; otherwise, an empty list.
    """
    logging.info(
        "Polling for cookies from the Brave browser (timeout=%d seconds)...", timeout
    )
    start_time = time.time()
    while True:
        cj = browser_cookie3.brave()
        cookies_list = list(cj)
        logging.info("Poll result: Found %d cookies", len(cookies_list))
        if len(cookies_list) > 0:
            return cookies_list
        if time.time() - start_time > timeout:
            logging.info("No cookies found after %d seconds.", timeout)
            return []
        logging.info("No cookies found yet. Sleeping %d seconds...", interval)
        time.sleep(interval)


def extract_cookies(output_file="/cloudflareopencv/data/cloudflare_cookies.json"):
    """
    Poll for cookies from Brave, convert them to serializable dictionaries, and save them to a JSON file.
    """
    cookies_list = poll_for_cookies(timeout=60, interval=3)
    try:
        # Convert cookies to dictionaries.
        serialized_cookies = [serialize_cookie(cookie) for cookie in cookies_list]
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            logging.info("Created output directory: %s", output_dir)
        with open(output_file, "w") as f:
            json.dump(serialized_cookies, f, indent=4)
        logging.info(
            "Cookies successfully extracted and saved to '%s' (found %d cookies).",
            output_file,
            len(serialized_cookies),
        )
    except Exception as e:
        logging.error("Failed to write cookies: %s", e)


def main():
    # 1) Wait for the initial page to load.
    initial_wait = 5
    logging.info("Waiting %d seconds for the page to fully load...", initial_wait)
    time.sleep(initial_wait)

    # 2) Check for the main Cloudflare challenge template.
    challenge_template = "/cloudflareopencv/images/cloudflare_verify_click_template_light.png"
    coords = find_template_coords(challenge_template, threshold=0.7)
    if coords:
        x, y = coords
        simulate_click(x, y)
        post_click_wait = 15  # increased wait time after clicking
        logging.info(
            "Waiting %d seconds after the click for any redirect...", post_click_wait
        )
        time.sleep(post_click_wait)
    else:
        logging.info(
            "Cloudflare verification template was not detected; no click action taken."
        )

    # 3) Extract cookies (polling until non-empty).
    extract_cookies()


if __name__ == "__main__":
    main()
