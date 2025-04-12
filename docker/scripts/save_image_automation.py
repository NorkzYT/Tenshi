#!/usr/bin/env python3
import subprocess
import sys
import time


def run_cmd(cmd):
    """Run a shell command and print it (for debugging)."""
    print(f"Running: {' '.join(cmd)}")
    subprocess.check_call(cmd)


def scroll_to_bottom():
    """
    Scroll to the bottom of the page repeatedly.
    This function sends the End key a few times with a short delay between them.
    """
    for i in range(5):
        run_cmd(["xdotool", "key", "End"])
        time.sleep(1)


def save_image_sequence(chapter_url, image_url):
    """
    Automates the browser to save an image using the same tab.
    Steps:
      1. Navigate to the chapter URL.
      2. Scroll to the bottom of the chapter page and wait for images to load.
      3. Run Cloudflare automation to bypass any challenges.
      4. Change the URL in the same tab to the image URL.
      5. Once the image page loads, send Ctrl+S to open the "Save as" dialog.
      6. Focus the filename bar, clear it, and type the target directory.
      7. Send Enter (Return) to confirm and save.
      8. Navigate back to the chapter page.
    """
    # Step 1: Navigate to the chapter page.
    run_cmd(["xdotool", "key", "ctrl+l"])
    time.sleep(0.5)
    run_cmd(["xdotool", "type", chapter_url])
    time.sleep(0.5)
    run_cmd(["xdotool", "key", "Return"])
    time.sleep(5)

    # Step 2: Scroll to the bottom of the chapter page to load all images.
    scroll_to_bottom()
    time.sleep(3)  # Give additional time for images to load.

    # Step 3: Run Cloudflare automation (if needed).
    run_cmd(["python3", "/cloudflareopencv/scripts/cloudflare_automation.py"])
    time.sleep(5)

    # Step 4: Reuse the same tab: change the URL to the image URL.
    run_cmd(["xdotool", "key", "ctrl+l"])
    time.sleep(0.5)
    run_cmd(["xdotool", "type", image_url])
    time.sleep(0.5)
    run_cmd(["xdotool", "key", "Return"])
    time.sleep(8)  # Wait for the image to load.

    # Step 5: Send Ctrl+S to open the Save dialog.
    run_cmd(["xdotool", "key", "ctrl+s"])
    time.sleep(3)  # Wait for the Save dialog to appear.

    # Step 6: Focus the filename bar, clear it, and type the target directory.
    run_cmd(["xdotool", "key", "ctrl+l"])
    time.sleep(0.5)
    run_cmd(["xdotool", "key", "Left"])
    run_cmd(["xdotool", "type", "/cloudflareopencv/data/"])
    time.sleep(5)

    # Step 7: Send Enter to confirm and save.
    # Obtain the currently focused window id for precision.
    window_id = (
        subprocess.check_output(["xdotool", "getwindowfocus"]).strip().decode("utf-8")
    )
    print(f"Active window id: {window_id}")
    run_cmd(["xdotool", "key", "--clearmodifiers", "--window", window_id, "Return"])
    time.sleep(10)

    # Step 8: Navigate back to the chapter page (using Alt+Left).
    run_cmd(["xdotool", "key", "Alt+Left"])
    time.sleep(5)


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
