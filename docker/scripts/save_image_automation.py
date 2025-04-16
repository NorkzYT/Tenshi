#!/usr/bin/env python3
"""
Automates saving an image by:
  1. Navigating to the chapter URL.
  2. Scrolling to load images.
  3. Running Cloudflare automation.
  4. Navigating to the image URL.
  5. Triggering the Save dialog.
  6. Inputting the target directory.
  7. Confirming the save.
  8. Navigating back to the chapter page.
  9. Renaming any files ending with " (1)".
"""

import subprocess
import sys
import time
import os
import re
from urllib.parse import urlparse
from scripts.utils import wait_for_template


RELOAD_TPL = "/tenshi/images/reload-button-template.png"


def run_cmd(cmd, delay=0):
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    if delay:
        time.sleep(delay)


def wait_for(condition_func, timeout=10, poll_interval=0.2):
    """Poll until condition_func returns True or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(poll_interval)
    return False


def is_chapter_page_loaded(expected_text="Chapter"):
    """Check if the current active window title contains expected_text."""
    try:
        window_id = (
            subprocess.check_output(["xdotool", "getactivewindow"])
            .strip()
            .decode("utf-8")
        )
        title = (
            subprocess.check_output(["xdotool", "getwindowname", window_id])
            .strip()
            .decode("utf-8")
        )
        print(f"Current window title: {title}")
        return expected_text in title
    except Exception as e:
        print(f"Error checking chapter page load: {e}")
        return False


def scroll_to_bottom():
    """Scroll to the bottom of the page using the End key repeatedly."""
    for _ in range(5):
        run_cmd(["xdotool", "key", "--delay", "10", "End"], delay=0.5)


def extract_chapter_folder(chapter_url):
    """Extract the chapter folder name from the chapter URL path."""
    parsed = urlparse(chapter_url)
    segments = parsed.path.rstrip("/").split("/")
    for segment in segments:
        if re.match(r"(?i)^chapter", segment):
            return segment
    return "default_chapter"


def remove_suffix_one(target_dir):
    """Rename files ending with ' (1)' before the extension."""
    for filename in os.listdir(target_dir):
        pattern = r"^(.*) \(1\)(\.\w+)$"
        match = re.match(pattern, filename)
        if match:
            new_filename = f"{match.group(1)}{match.group(2)}"
            old_path = os.path.join(target_dir, filename)
            new_path = os.path.join(target_dir, new_filename)
            print(f"Renaming {old_path} to {new_path}")
            try:
                os.rename(old_path, new_path)
            except Exception as err:
                print(f"Failed to rename {old_path}: {err}")


def navigate_to_url(url):
    """Navigates to the given URL using xdotool commands."""
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+l"], delay=0.2)
    run_cmd(["xdotool", "type", "--delay", "10", url], delay=0.2)
    run_cmd(["xdotool", "key", "--delay", "10", "Return"], delay=2)


def save_image_sequence(chapter_url, image_url):
    """Sequence of steps to automate image saving."""
    chapter_folder = extract_chapter_folder(chapter_url)
    if not chapter_folder.endswith("/"):
        chapter_folder += "/"
    target_dir = os.path.join("/tenshi/data", chapter_folder)
    os.makedirs(target_dir, exist_ok=True)
    print(f"Target directory: {target_dir}")

    # Navigate to chapter page.
    navigate_to_url(chapter_url)

    if not wait_for(lambda: is_chapter_page_loaded(expected_text="Chapter"), timeout=5):
        print("Warning: Chapter page did not load within timeout.")

    scroll_to_bottom()
    time.sleep(1)

    # run Cloudflare automation (internal wait)
    run_cmd(["python3", "/tenshi/scripts/cloudflare_automation.py"], delay=0)

    # navigate to image URL
    navigate_to_url(image_url)

    # wait for reload‑icon before Save
    wait_for_template(RELOAD_TPL, threshold=0.75, interval=0.5, timeout=20)

    # trigger Save dialog
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+s"], delay=1)

    # Focus filename bar and input target directory.
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+l"], delay=0.2)
    run_cmd(["xdotool", "key", "--delay", "10", "Left"])
    run_cmd(["xdotool", "type", "--delay", "10", target_dir], delay=1)

    # Confirm save.
    window_id = (
        subprocess.check_output(["xdotool", "getwindowfocus"]).strip().decode("utf-8")
    )
    print(f"Active window id: {window_id}")
    run_cmd(
        [
            "xdotool",
            "key",
            "--clearmodifiers",
            "--delay",
            "10",
            "--window",
            window_id,
            "Return",
        ],
        delay=2,
    )

    # Navigate back to chapter page.
    run_cmd(["xdotool", "key", "--delay", "10", "Alt+Left"], delay=1)

    # Post-process: remove suffix "(1)" from files.
    remove_suffix_one(target_dir)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: save_image_automation.py <chapter_url> <image_url>")
        sys.exit(1)
    try:
        save_image_sequence(sys.argv[1], sys.argv[2])
    except Exception as e:
        print(f"Error during image-saving automation: {e}")
        sys.exit(1)
