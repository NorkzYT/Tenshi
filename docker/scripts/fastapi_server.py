#!/usr/bin/env python3
"""
FastAPI Server for Cloudflare Automation Trigger

This server listens for HTTP GET requests on the '/trigger' endpoint with a query parameter `url`.
Upon receiving a valid URL, it:
  1. Focuses the Brave browser's address bar via xdotool.
  2. Types the provided URL and presses Enter.
  3. Waits briefly for the page to load.
  4. Triggers the Cloudflare automation by launching a helper shell script.

Example usage:
    GET /trigger?url=https://example.com
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import os
import subprocess
import logging
import time
import uvicorn

# Create the FastAPI app.
app = FastAPI()

# Configure logging.
logging.basicConfig(level=logging.INFO)


@app.get("/trigger")
async def trigger_automation(
    url: str = Query(
        ...,
        description="URL to load in the browser (must start with http:// or https://)",
    ),
    js: str = Query(..., description="JavaScript snippet to execute on the page."),
    wait: str = Query("", description="(Optional) CSS selector to wait for."),
    sleep: int = Query(
        5000, description="(Optional) Delay in milliseconds for page stabilization."
    ),
):
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=400, detail="Invalid URL scheme. Must be http or https."
        )
    try:
        update_browser_url(url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Browser update error: {e}")

    # Give the browser a moment to load the URL.
    time.sleep(5)
    try:
        logging.info("Starting Cloudflare automation synchronously...")
        # Use check_output to wait for cloudflare_start.sh to finish.
        automationCmd = [
            "/tenshi/config/cloudflare_start.sh",
            url,
            wait,
            str(sleep),
            js,
        ]
        output = subprocess.check_output(
            automationCmd, stderr=subprocess.STDOUT, timeout=120
        )
        logging.info(
            "Cloudflare automation completed with output:\n%s", output.decode("utf-8")
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Automation error: {e.output.decode('utf-8')}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    # When the automation finishes, return success.
    return {"status": "Triggered", "url": url, "js": js, "wait": wait, "sleep": sleep}


@app.get("/save_image")
async def save_image(
    chapter_url: str = Query(..., description="Chapter URL for verification."),
    image_url: str = Query(..., description="Full image URL from CDN."),
):
    if "cdn." not in image_url:
        raise HTTPException(
            status_code=400, detail="Image URL does not belong to a CDN."
        )
    if "cdn." in chapter_url:
        raise HTTPException(
            status_code=400, detail="Chapter URL should not be a CDN URL."
        )

    try:
        subprocess.check_output(
            [
                "python3",
                "/tenshi/scripts/save_image_automation.py",
                chapter_url,
                image_url,
            ],
            stderr=subprocess.STDOUT,
            timeout=180,
        )
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Automation error: {e.output.decode('utf-8')}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    return {"status": "Saved", "chapter_url": chapter_url, "image_url": image_url}


@app.get("/get_image")
async def get_image(
    chapter: str = Query(
        ...,
        description="Chapter folder name (e.g., 'chapter_2') from /tenshi/data/",
    ),
    filename: str = Query(
        None,
        description="(Optional) Filename of the image (e.g., 'page_001.jpg'). If omitted, returns all image filenames in the chapter.",
    ),
):
    # Build the absolute chapter folder path.
    chapter_path = os.path.join("/tenshi/data", chapter)
    if not os.path.isdir(chapter_path):
        raise HTTPException(status_code=404, detail="Chapter folder not found")

    if filename:
        # Build the absolute image path.
        image_path = os.path.join(chapter_path, filename)
        # Check if the file exists.
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        # Return the image file as a response.
        return FileResponse(image_path, media_type="image/jpeg")
    else:
        # List all image files in the chapter folder (filtering common image extensions).
        try:
            files = os.listdir(chapter_path)
            images = [
                f
                for f in files
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
            ]
            return {"chapter": chapter, "images": images}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error reading chapter folder: {e}"
            )


def update_browser_url(target_url: str):
    try:
        # Find the visible Brave browser window.
        window_ids = (
            subprocess.check_output(
                ["xdotool", "search", "--onlyvisible", "--class", "Brave-browser"]
            )
            .decode()
            .split()
        )
        if not window_ids:
            raise Exception("No visible Brave browser window found.")
        window_id = window_ids[0]
        logging.info("Found Brave window id: %s", window_id)

        # Activate the browser window.
        ret = subprocess.call(["xdotool", "windowactivate", window_id])
        if ret != 0:
            logging.warning("Window activation failed with exit code %d.", ret)
        time.sleep(0.5)

        # Focus the address bar with Ctrl+L.
        logging.info("Focusing browser address bar (Ctrl+L)...")
        subprocess.check_call(["xdotool", "key", "--delay", "10", "ctrl+l"])
        time.sleep(0.5)

        # Clear existing text in the address bar using Ctrl+A and BackSpace.
        logging.info("Clearing existing text with Ctrl+A and BackSpace...")
        subprocess.check_call(["xdotool", "key", "--delay", "10", "ctrl+a"])
        time.sleep(0.1)
        subprocess.check_call(["xdotool", "key", "--delay", "10", "BackSpace"])
        time.sleep(0.5)

        # Type the new URL.
        logging.info("Typing URL: %s", target_url)
        subprocess.check_call(["xdotool", "type", "--delay", "10", target_url])
        time.sleep(0.5)

        # Simulate pressing Enter.
        logging.info("Simulating Enter key...")
        subprocess.check_call(["xdotool", "key", "--delay", "10", "Return"])
    except Exception as e:
        logging.error("Error updating browser URL: %s", e)
        raise


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
