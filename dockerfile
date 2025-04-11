# Use the Phusion Baseimage for Ubuntu Jammy.
FROM phusion/baseimage:jammy-1.0.4

LABEL maintainer="Richard Lora <richard@pcscorp.dev>"
ENV DEBIAN_FRONTEND=noninteractive

# -------------------------------------------------------------
# Create a non-root user 'cloudflareopencv' for running the automation.
RUN useradd -m -s /bin/bash cloudflareopencv && \
    echo "cloudflareopencv:password" | chpasswd && \
    chown -R cloudflareopencv:cloudflareopencv /home/cloudflareopencv

ENV USER=cloudflareopencv

# -------------------------------------------------------------
# Install OS-level dependencies.
RUN apt-get update && \
    apt-get install -y \
      sudo \
      curl \
      gnupg2 \
      lsb-release \
      xdotool \
      xvfb \
      python3-opencv \
      scrot \
      dbus-x11 \
      python3-pip \
      x11-xserver-utils \
      apt-transport-https && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------
# Install Brave Browser via its official APT repository.
RUN curl -fsSLo /usr/share/keyrings/brave-browser-archive-keyring.gpg \
        https://brave-browser-apt-release.s3.brave.com/brave-browser-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/brave-browser-archive-keyring.gpg arch=amd64,arm64] https://brave-browser-apt-release.s3.brave.com/ stable main" | \
        tee /etc/apt/sources.list.d/brave-browser-release.list && \
    apt-get update && \
    apt-get install -y brave-browser && \
    rm -rf /var/lib/apt/lists/*

# -------------------------------------------------------------
# Install Python dependencies from requirements.txt.
COPY docker/config/requirements.txt /tmp/requirements.txt
RUN pip3 install --upgrade pip && \
    pip3 install -r /tmp/requirements.txt

# -------------------------------------------------------------
# Copy repository files into the container.
COPY docker/config/entrypoint.sh /cloudflareopencv/config/entrypoint.sh
COPY docker/config/cloudflare_start.sh /cloudflareopencv/config/cloudflare_start.sh
COPY docker/scripts /cloudflareopencv/scripts
COPY docker/images /cloudflareopencv/images

# Set execution permissions on shell and Python scripts.
RUN chmod +x /cloudflareopencv/config/entrypoint.sh && \
    chmod +x /cloudflareopencv/config/cloudflare_start.sh && \
    find /cloudflareopencv/scripts -type f -name "*.sh" -exec chmod +x {} \; && \
    find /cloudflareopencv/scripts -type f -name "*.py" -exec chmod +x {} \;

# -------------------------------------------------------------
# Setup additional dependencies: DBus and pulseaudio.
ENV DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
RUN apt-get update && apt-get install -y pulseaudio && \
    mkdir -p /var/run/dbus && \
    rm -rf /var/lib/apt/lists/*

# Create a secure XDG_RUNTIME_DIR (required by some applications) with 700 permissions.
RUN mkdir -p /run/user/1000 && chmod 700 /run/user/1000
ENV XDG_RUNTIME_DIR=/run/user/1000

# After installing dependencies and before switching to USER cloudflareopencv:
RUN mkdir -p /cloudflareopencv/data && chown -R cloudflareopencv:cloudflareopencv /cloudflareopencv/data
RUN mkdir -p /cloudflareopencv/data/screenshots && chown -R cloudflareopencv:cloudflareopencv /cloudflareopencv/data

# Create the X11 socket directory with proper permissions (as root)
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

# -------------------------------------------------------------
# --- Install VNC server and HTML5 frontend packages ---
RUN apt-get update && apt-get install -y x11vnc novnc websockify && \
    rm -rf /var/lib/apt/lists/*

# Expose ports for VNC (5900) and noVNC (6080)
EXPOSE 5900 6080

# Create a user-owned runtime directory for DBus and other services.
RUN mkdir -p /home/cloudflareopencv/runtime && chmod 700 /home/cloudflareopencv/runtime
# Set XDG_RUNTIME_DIR to this new directory.
ENV XDG_RUNTIME_DIR=/home/cloudflareopencv/runtime

# Set the container working directory.
WORKDIR /home/cloudflareopencv

# -------------------------------------------------------------
# Set the container entrypoint.
ENTRYPOINT ["/cloudflareopencv/config/entrypoint.sh"]
