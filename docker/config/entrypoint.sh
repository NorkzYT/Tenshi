#!/bin/bash
set -e
# -------------------------------------------------------------
#
# Sets up user DBus session, Xvfb, Brave Browser with remote debugging,
# and starts VNC, noVNC and FastAPI services.
# -------------------------------------------------------------

start_dbus() {
    if [ -z "$DBUS_SESSION_BUS_ADDRESS" ]; then
        echo "Starting DBus session bus..."
        eval "$(dbus-launch --sh-syntax)"
        echo "DBUS_SESSION_BUS_ADDRESS: $DBUS_SESSION_BUS_ADDRESS"
    fi
}

setup_display() {
    if [ -z "$DISPLAY" ]; then
        export DISPLAY=:99
        echo "DISPLAY variable set to $DISPLAY"
    fi

    if [ ! -d /tmp/.X11-unix ]; then
        echo "Creating /tmp/.X11-unix..."
        mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
    fi

    if ! pgrep -x "Xvfb" >/dev/null; then
        echo "Starting Xvfb on DISPLAY $DISPLAY..."
        Xvfb "$DISPLAY" -screen 0 1920x1080x24 &
        sleep 2
    fi
}

setup_brave_preferences() {
    CUSTOM_USER_DATA="/tenshi/BraveData"
    mkdir -p "$CUSTOM_USER_DATA/Default"
    PREF_FILE="$CUSTOM_USER_DATA/Default/Preferences"
    if [ ! -f "$PREF_FILE" ]; then
        echo "Creating Preferences file..."
        cat <<EOF >"$PREF_FILE"
{
  "download": {
    "default_directory": "/tenshi"
  }
}
EOF
    else
        echo "Updating Preferences file for download directory..."
        tmp_file=$(mktemp)
        jq '.download.default_directory="/tenshi"' "$PREF_FILE" >"$tmp_file" && mv "$tmp_file" "$PREF_FILE"
    fi
}

start_services() {
    TARGET_URL=${TARGET_URL:-"about:blank"}
    echo "Launching Brave Browser with URL: $TARGET_URL"
    brave-browser --user-data-dir="$CUSTOM_USER_DATA" \
        --enable-unsafe-swiftshader --no-sandbox --disable-setuid-sandbox \
        --disable-gpu --no-first-run --remote-debugging-port=9223 "$TARGET_URL" &
    echo "Starting socat to forward 9222->127.0.0.1:9223"
    socat TCP4-LISTEN:9222,fork TCP4:127.0.0.1:9223 &

    if [ -z "$VNC_PASSWORD" ]; then
        echo "VNC_PASSWORD not set. Exiting."
        exit 1
    fi
    echo "Storing VNC password..."
    x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vnc_pass
    echo "Starting x11vnc..."
    x11vnc -display "$DISPLAY" -forever -rfbauth /tmp/vnc_pass -listen 0.0.0.0 -xkb &
    echo "Starting noVNC..."
    websockify --web=/usr/share/novnc 6080 localhost:5900 &
    echo "Starting FastAPI server..."
    python3 /tenshi/scripts/fastapi_server.py &
}

start_dbus
setup_display
setup_brave_preferences
start_services

# Keep container alive.
tail -f /dev/null
