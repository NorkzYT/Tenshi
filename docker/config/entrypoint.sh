#!/bin/bash
# -------------------------------------------------------------
# entrypoint.sh
#
# This script sets up the user DBus session bus, Xvfb, and then
# launches Brave Browser with a maximized window and remote debugging.
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

# --- Custom Brave Browser Configuration ---

# Define custom user data directory for Brave.
CUSTOM_USER_DATA="/tenshi/BraveData"

# Create the custom user data directory and the default profile folder.
mkdir -p "$CUSTOM_USER_DATA/Default"

# Set the path for the Brave Preferences file.
PREF_FILE="$CUSTOM_USER_DATA/Default/Preferences"

# If the Preferences file does not exist, create it with the desired setting.
if [ ! -f "$PREF_FILE" ]; then
    echo "Creating Preferences file with custom download directory..."
    cat <<EOF >"$PREF_FILE"
{
  "download": {
    "default_directory": "/tenshi"
  }
}
EOF
else
    # If the file exists, update the download default_directory using jq.
    echo "Updating existing Preferences file to set download.default_directory to /tenshi..."
    tmp_file=$(mktemp)
    jq '.download.default_directory="/tenshi"' "$PREF_FILE" >"$tmp_file" && mv "$tmp_file" "$PREF_FILE"
fi

# --- Launch Brave Browser with the custom user data directory ---
TARGET_URL=${TARGET_URL:-"about:blank"}
echo "Launching Brave Browser with custom user-data directory and URL: $TARGET_URL"
brave-browser --user-data-dir="$CUSTOM_USER_DATA" \
    --enable-unsafe-swiftshader --no-sandbox --disable-setuid-sandbox \
    --disable-gpu --no-first-run --remote-debugging-port=9223 "$TARGET_URL" &

# Start socat to forward port 9222 from all interfaces to Brave on 127.0.0.1:9223.
echo "Starting socat to forward port 9222 from 0.0.0.0 to 127.0.0.1:9223"
socat TCP4-LISTEN:9222,fork TCP4:127.0.0.1:9223 &

# Continue with the remaining startup steps (VNC, noVNC, FastAPI, etc.).
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

echo "Starting FastAPI server..."
python3 /tenshi/scripts/fastapi_server.py &

# Keep the container running.
tail -f /dev/null
