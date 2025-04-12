#!/bin/bash
# -------------------------------------------------------------
# cloudflare_start.sh
#
# This script launches the Cloudflare automation Python script,
# waits for page stabilization, and then invokes the modular TypeScript
# Puppeteer controller with parameters provided from the FastAPI endpoint.
# -------------------------------------------------------------

echo "Launching Cloudflare Automation Script..."
python3 /cloudflareopencv/scripts/cloudflare_automation.py

# Wait a moment after Cloudflare verification and cookie extraction.
echo "Waiting 5 seconds for page stabilization post-verification..."
sleep 5
