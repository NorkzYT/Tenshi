#!/bin/bash
# -------------------------------------------------------------
# entrypoint.sh
#
# This script sets up the user DBus session bus, Xvfb, and then
# launches Brave Browser with a maximized window using additional
# flags required to bypass sandbox restrictions in Docker.
#
# It also starts VNC services and the FastAPI server.
# -------------------------------------------------------------

# --- Start a user DBus session bus if not already set ---
if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
    echo "Starting DBus session bus..."
    eval "$(dbus-launch --sh-syntax)"
    echo "DBUS_SESSION_BUS_ADDRESS: $DBUS_SESSION_BUS_ADDRESS"
fi

# Ensure DISPLAY is set (default to :99).
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:99
    echo "DISPLAY environment variable set to $DISPLAY"
fi

# Ensure the X11 socket directory exists with proper permissions.
if [ ! -d /tmp/.X11-unix ]; then
    echo "Creating /tmp/.X11-unix with correct permissions..."
    mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
fi

# Start Xvfb if not already running.
if ! pgrep -x "Xvfb" >/dev/null; then
    echo "Starting Xvfb on DISPLAY $DISPLAY..."
    Xvfb $DISPLAY -screen 0 1920x1080x24 &
    sleep 2
fi

# Launch Brave Browser with a maximized window and additional flags.
TARGET_URL=${TARGET_URL:-"about:blank"}
echo "Launching Brave Browser maximized with URL: $TARGET_URL"
brave-browser --start-maximized --no-sandbox --disable-setuid-sandbox --disable-gpu --no-first-run "$TARGET_URL" &

# Allow some time for Brave to initialize.
sleep 5

# --- Start VNC server for display sharing with password ---
if [ -z "$VNC_PASSWORD" ]; then
    echo "VNC_PASSWORD environment variable not set. Exiting for security reasons."
    exit 1
fi

echo "Storing VNC password..."
x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vnc_pass

echo "Starting x11vnc with password authentication..."
x11vnc -display $DISPLAY -forever -rfbauth /tmp/vnc_pass -listen 0.0.0.0 -xkb &

echo "Starting noVNC (websockify)..."
websockify --web=/usr/share/novnc 6080 localhost:5900 &

# --- Start FastAPI server for Cloudflare automation trigger ---
echo "Starting FastAPI server..."
python3 /cloudflareopencv/scripts/fastapi_server.py &

# Keep the container running.
tail -f /dev/null
