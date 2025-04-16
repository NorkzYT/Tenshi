#!/bin/bash
set -e
# -------------------------------------------------------------
#
# Launches the Cloudflare automation script and waits for stabilization.
# -------------------------------------------------------------

echo "Launching Cloudflare Automation Script..."
python3 /tenshi/scripts/cloudflare_automation.py
