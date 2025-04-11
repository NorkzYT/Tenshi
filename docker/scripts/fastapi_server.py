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
import subprocess
import logging
import time

from fastapi import FastAPI, HTTPException, Query
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
    )
):
    # Validate that the URL has a proper scheme.
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(
            status_code=400, detail="Invalid URL scheme. Must be http or https."
        )

    try:
        # Use xdotool to simulate focusing the address bar (Ctrl+L),
        # then type the new URL and press Return.
        logging.info("Focusing Brave address bar (simulating Ctrl+L)...")
        subprocess.check_call(["xdotool", "key", "ctrl+l"])
        time.sleep(0.5)

        logging.info("Typing URL: %s", url)
        subprocess.check_call(["xdotool", "type", url])
        time.sleep(0.5)

        logging.info("Simulating Enter key to navigate...")
        subprocess.check_call(["xdotool", "key", "Return"])
    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update the browser URL: {e}"
        )

    # Allow the page time to load.
    time.sleep(5)

    try:
        # Now start the Cloudflare automation process via the helper shell script.
        logging.info("Starting Cloudflare automation...")
        subprocess.Popen(["/cloudflareopencv/config/cloudflare_start.sh"])
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start Cloudflare automation: {e}"
        )

    return {"status": "Triggered", "url": url}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
