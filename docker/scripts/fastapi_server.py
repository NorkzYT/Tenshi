#!/usr/bin/env python3
"""
FastAPI Server for Cloudflare Automation Trigger

Listens for HTTP GET requests on endpoints (trigger, save_image, and get_image) to automate browser actions.
"""

import os
import re
import subprocess
import logging
import time
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

# Create FastAPI app and configure logging.
app = FastAPI()
logging.basicConfig(level=logging.INFO)


def run_xdotool(args, delay=0):
    """Wrapper for xdotool command execution with delay support."""
    logging.info("Executing xdotool command: %s", " ".join(args))
    try:
        subprocess.check_call(["xdotool"] + args)
        if delay:
            time.sleep(delay)
    except subprocess.CalledProcessError as e:
        logging.error("xdotool command failed: %s", e)
        raise


def activate_browser():
    """Finds the visible Brave browser window and activates it."""
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
    if subprocess.call(["xdotool", "windowactivate", window_id]) != 0:
        logging.warning("Window activation failed.")
    time.sleep(0.5)
    return window_id


def focus_address_bar():
    """Focus the address bar by simulating Ctrl+L and clearing existing text."""
    logging.info("Focusing and clearing browser address bar...")
    run_xdotool(["key", "--delay", "10", "ctrl+l"], delay=0.5)
    run_xdotool(["key", "--delay", "10", "ctrl+a"], delay=0.1)
    run_xdotool(["key", "--delay", "10", "BackSpace"], delay=0.5)


def type_and_submit_url(url: str):
    """Types the provided URL into the browser and simulates pressing Enter."""
    logging.info("Typing URL: %s", url)
    run_xdotool(["type", "--delay", "10", url], delay=0.5)
    run_xdotool(["key", "--delay", "10", "Return"])


def update_browser_url(target_url: str):
    """High-level function to update the browser's URL with proper focus and typing."""
    try:
        activate_browser()
        focus_address_bar()
        type_and_submit_url(target_url)
    except Exception as e:
        logging.error("Error updating browser URL: %s", e)
        raise


@app.get("/trigger")
async def trigger_automation(
    url: str = Query(
        ...,
        description="URL to load in the browser (must start with http:// or https://)",
    ),
    js: str = Query("", description="JavaScript snippet to execute on the page."),
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

    time.sleep(5)  # Allow the page to load

    try:
        logging.info("Starting Cloudflare automation synchronously...")
        automation_cmd = [
            "/tenshi/config/cloudflare_start.sh",
            url,
            wait,
            str(sleep),
            js,
        ]
        output = subprocess.check_output(
            automation_cmd, stderr=subprocess.STDOUT, timeout=120
        )
        logging.info("Cloudflare automation output:\n%s", output.decode("utf-8"))
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Automation error: {e.output.decode('utf-8')}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

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
        ..., description="Chapter folder name (e.g., 'chapter_2') from /tenshi/data/"
    ),
    filename: str = Query(
        None, description="(Optional) Filename of the image (e.g., 'page_001.jpg')."
    ),
):
    chapter_path = os.path.join("/tenshi/data", chapter)
    if not os.path.isdir(chapter_path):
        raise HTTPException(status_code=404, detail="Chapter folder not found")

    if filename:
        image_path = os.path.join(chapter_path, filename)
        if not os.path.isfile(image_path):
            raise HTTPException(status_code=404, detail="Image not found")
        return FileResponse(image_path, media_type="image/jpeg")
    else:
        try:
            images = [
                f
                for f in os.listdir(chapter_path)
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif"))
            ]
            return {"chapter": chapter, "images": images}
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error reading chapter folder: {e}"
            )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
