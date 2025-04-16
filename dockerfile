# Use the Phusion Baseimage for Ubuntu Jammy.
FROM phusion/baseimage:jammy-1.0.4

LABEL maintainer="Richard Lora <richard@pcscorp.dev>"
ENV DEBIAN_FRONTEND=noninteractive

# -------------------------------------------------------------
# Create a non-root user 'tenshi' for running the automation.
ARG PASSWORD
RUN useradd -m -s /bin/bash tenshi && \
    echo "tenshi:${PASSWORD}" | chpasswd && \
    chown -R tenshi:tenshi /home/tenshi
ENV USER=tenshi

# -------------------------------------------------------------
# Install OS-level dependencies and Brave Browser.
RUN apt-get update && apt-get install -y \
      sudo curl gnupg2 lsb-release xdotool xvfb python3-opencv \
      scrot dbus-x11 python3-pip x11-xserver-utils apt-transport-https \
      socat imagemagick jq \
      x11vnc novnc websockify pulseaudio && \
    rm -rf /var/lib/apt/lists/* && \
    \
    # Install Brave Browser via its official APT repository.
    curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
        https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64,arm64] https://brave-browser-apt-release.s3.brave.com/ stable main" | \
        tee /etc/apt/sources.list.d/brave-browser-release.list && \
    apt-get update && apt-get install -y brave-browser && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------
# Install Python dependencies from requirements.txt.
COPY docker/config/requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r /tmp/requirements.txt

# -------------------------------------------------------------
# Copy repository files into the container.
COPY docker/config/entrypoint.sh /tenshi/config/entrypoint.sh
COPY docker/config/cloudflare_start.sh /tenshi/config/cloudflare_start.sh
COPY docker/scripts /tenshi/scripts
COPY docker/images /tenshi/images

# Set execution permissions on shell and Python scripts.
RUN chmod +x /tenshi/config/entrypoint.sh /tenshi/config/cloudflare_start.sh && \
    find /tenshi/scripts -type f \( -name "*.sh" -o -name "*.py" \) -exec chmod +x {} \;

# -------------------------------------------------------------
# Setup additional configurations and directories.
ENV DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
RUN mkdir -p /run/user/1000 /tenshi/data/screenshots /tenshi/data && \
    chown -R tenshi:tenshi /tenshi/data && \
    mkdir -p /home/tenshi/runtime && chmod 700 /home/tenshi/runtime && \
    mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

ENV XDG_RUNTIME_DIR=/home/tenshi/runtime
# Add our script folder to PYTHONPATH so `import scripts.utils` works
ENV PYTHONPATH=/tenshi

# -------------------------------------------------------------
# Expose ports for VNC and noVNC.
EXPOSE 5900 6080

# -------------------------------------------------------------
# Set the working directory and entrypoint.
WORKDIR /home/tenshi
ENTRYPOINT ["/tenshi/config/entrypoint.sh"]
