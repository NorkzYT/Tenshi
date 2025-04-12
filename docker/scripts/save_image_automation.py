#!/usr/bin/env python3
import subprocess
import sys
import time


def run_cmd(cmd):
    """Run a shell command and print it (for debugging)."""
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def save_image_sequence(chapter_url, image_url):
    """
    Automates the browser to save an image using both the chapter URL and image URL.
    Steps:
      1. Navigate to the chapter URL.
      2. Run Cloudflare automation to bypass challenges.
      3. Open a new tab and load the image URL.
      4. Send Ctrl+S to open the "Save as" dialog.
      5. Focus the filename bar, clear it, and type the target directory.
      6. Send Enter (Return) to confirm saving.
    """
    # Step 1: Navigate to the chapter URL.
    run_cmd(["xdotool", "key", "ctrl+l"])
    time.sleep(0.5)
    run_cmd(["xdotool", "type", chapter_url])
    time.sleep(0.5)
    run_cmd(["xdotool", "key", "Return"])
    time.sleep(5)

    # Step 2: Run Cloudflare automation.
    run_cmd(["python3", "/cloudflareopencv/scripts/cloudflare_automation.py"])
    time.sleep(5)

    # Step 3: Open a new tab.
    run_cmd(["xdotool", "key", "ctrl+t"])
    time.sleep(1)

    # Step 4: Load the image URL.
    run_cmd(["xdotool", "type", image_url])
    time.sleep(0.5)
    run_cmd(["xdotool", "key", "Return"])
    time.sleep(8)  # Increased wait time for image page to load.

    # Step 5: Send Ctrl+S to open the Save dialog.
    run_cmd(["xdotool", "key", "ctrl+s"])
    time.sleep(3)  # Wait for the Save dialog to appear.

    # Step 6: In the save dialog, focus the filename bar and type the target directory.
    run_cmd(["xdotool", "key", "ctrl+l"])
    time.sleep(0.5)
    run_cmd(["xdotool", "key", "Left"])
    run_cmd(["xdotool", "type", "/cloudflareopencv/data/"])
    time.sleep(5)

    # Step 7: Send Return to confirm saving.
    # Get the currently focused window ID.
    window_id = (
        subprocess.check_output(["xdotool", "getwindowfocus"]).strip().decode("utf-8")
    )
    print(f"Active window id: {window_id}")
    # Send the Return key specifically to that window, clearing any modifiers.
    run_cmd(["xdotool", "key", "--clearmodifiers", "--window", window_id, "Return"])
    time.sleep(10)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: save_image_automation.py <chapter_url> <image_url>")
        sys.exit(1)
    chapter_url = sys.argv[1]
    image_url = sys.argv[2]
    try:
        save_image_sequence(chapter_url, image_url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
