#!/usr/bin/env python3
"""
Revised save_image_automation.py

This script automates the process of saving an image by:
  1. Navigating to a chapter URL.
  2. Scrolling down to load images.
  3. Running Cloudflare automation.
  4. Navigating to the image URL.
  5. Triggering the Save dialog.
  6. Inputting the target directory (including chapter folder).
  7. Confirming the save.
  8. Navigating back to the chapter page.
"""

import subprocess
import sys
import time
import os
import re
from urllib.parse import urlparse


def run_cmd(cmd):
    """Run a shell command and print it (for debugging)."""
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def wait_for(condition_func, timeout=10, poll_interval=0.2):
    """Poll until condition_func returns True or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        if condition_func():
            return True
        time.sleep(poll_interval)
    return False


def is_chapter_page_loaded(expected_text="Chapter"):
    """
    Placeholder function that checks if the chapter page has loaded.
    For example, you might check that the active window title contains a specific text.
    """
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
        print(f"Error while checking chapter page load: {e}")
        return False


def scroll_to_bottom():
    """
    Scroll to the bottom of the page repeatedly using the End key.
    """
    for _ in range(5):
        run_cmd(["xdotool", "key", "--delay", "10", "End"])
        time.sleep(0.5)


def extract_chapter_folder(chapter_url):
    """
    Extracts the chapter folder name from the chapter_url.
    It looks for a path segment that starts with "chapter" (case-insensitive).
    If not found, returns "default_chapter".
    """
    parsed = urlparse(chapter_url)
    segments = parsed.path.rstrip("/").split("/")
    for segment in segments:
        if re.match(r"(?i)^chapter", segment):
            return segment
    return "default_chapter"


def save_image_sequence(chapter_url, image_url):
    """
    Executes the sequence for saving an image:
      1. Navigate to the chapter URL.
      2. Scroll to load images.
      3. Run Cloudflare automation.
      4. Switch to the image URL.
      5. Open and handle the Save dialog.
      6. Input the target directory with the chapter folder.
      7. Confirm save and navigate back.
    """
    # Extract chapter folder from chapter_url.
    chapter_folder = extract_chapter_folder(chapter_url)
    # Ensure chapter_folder ends with a "/" as required.
    if not chapter_folder.endswith("/"):
        chapter_folder += "/"
    target_dir = os.path.join("/tenshi/data", chapter_folder)

    # Create the chapter folder if it doesn't exist.
    os.makedirs(target_dir, exist_ok=True)
    print(f"Target directory for saving image: {target_dir}")

    # Step 1: Navigate to the chapter page.
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+l"])
    time.sleep(0.2)
    run_cmd(["xdotool", "type", "--delay", "10", chapter_url])
    time.sleep(0.2)
    run_cmd(["xdotool", "key", "--delay", "10", "Return"])

    # Wait for the chapter page to load.
    if not wait_for(lambda: is_chapter_page_loaded(expected_text="Chapter"), timeout=5):
        print("Warning: Chapter page did not load within the timeout.")

    # Step 2: Scroll down to load images.
    scroll_to_bottom()
    time.sleep(1)

    # Step 3: Run Cloudflare automation.
    run_cmd(["python3", "/tenshi/scripts/cloudflare_automation.py"])
    time.sleep(2)

    # Step 4: Navigate to the image URL.
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+l"])
    time.sleep(0.2)
    run_cmd(["xdotool", "type", "--delay", "10", image_url])
    time.sleep(0.2)
    run_cmd(["xdotool", "key", "--delay", "10", "Return"])
    time.sleep(2)

    # Step 5: Trigger the Save dialog via Ctrl+S.
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+s"])
    time.sleep(1)

    # Step 6: Focus the filename bar and enter target directory with chapter folder.
    run_cmd(["xdotool", "key", "--delay", "10", "ctrl+l"])
    time.sleep(0.2)
    run_cmd(["xdotool", "key", "--delay", "10", "Left"])
    run_cmd(["xdotool", "type", "--delay", "10", target_dir])
    time.sleep(1)

    # Step 7: Confirm the save by sending Enter.
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
        ]
    )
    time.sleep(2)

    # Step 8: Navigate back to the chapter page.
    run_cmd(["xdotool", "key", "--delay", "10", "Alt+Left"])
    time.sleep(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: save_image_automation.py <chapter_url> <image_url>")
        sys.exit(1)
    chapter_url = sys.argv[1]
    image_url = sys.argv[2]
    try:
        save_image_sequence(chapter_url, image_url)
    except Exception as e:
        print(f"Error during image-saving automation: {e}")
        sys.exit(1)
