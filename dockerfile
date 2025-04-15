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
# Install OS-level dependencies.
RUN apt-get update && apt-get install -y \
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
      apt-transport-https \
      socat \
      imagemagick \
    && rm -rf /var/lib/apt/lists/*

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
COPY docker/config/entrypoint.sh /tenshi/config/entrypoint.sh
COPY docker/config/cloudflare_start.sh /tenshi/config/cloudflare_start.sh
COPY docker/scripts /tenshi/scripts
COPY docker/images /tenshi/images

# Set execution permissions on shell and Python scripts.
RUN chmod +x /tenshi/config/entrypoint.sh && \
    chmod +x /tenshi/config/cloudflare_start.sh && \
    find /tenshi/scripts -type f -name "*.sh" -exec chmod +x {} \; && \
    find /tenshi/scripts -type f -name "*.py" -exec chmod +x {} \;

# -------------------------------------------------------------
# Setup additional dependencies: DBus and pulseaudio.
ENV DBUS_SYSTEM_BUS_ADDRESS=unix:path=/host/run/dbus/system_bus_socket
RUN apt-get update && apt-get install -y pulseaudio && \
    mkdir -p /var/run/dbus && \
    rm -rf /var/lib/apt/lists/*

# Create a secure XDG_RUNTIME_DIR (required by some applications) with 700 permissions.
RUN mkdir -p /run/user/1000 && chmod 700 /run/user/1000
ENV XDG_RUNTIME_DIR=/run/user/1000

# After installing dependencies and before switching to USER tenshi:
RUN mkdir -p /tenshi/data && chown -R tenshi:tenshi /tenshi/data
RUN mkdir -p /tenshi/data/screenshots && chown -R tenshi:tenshi /tenshi/data

# Create the X11 socket directory with proper permissions (as root)
RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

# -------------------------------------------------------------
# --- Install VNC server and HTML5 frontend packages ---
RUN apt-get update && apt-get install -y x11vnc novnc websockify && \
    rm -rf /var/lib/apt/lists/*

# Expose ports for VNC (5900) and noVNC (6080)
EXPOSE 5900 6080 

# Create a user-owned runtime directory for DBus and other services.
RUN mkdir -p /home/tenshi/runtime && chmod 700 /home/tenshi/runtime
# Set XDG_RUNTIME_DIR to this new directory.
ENV XDG_RUNTIME_DIR=/home/tenshi/runtime

# Set the container working directory.
WORKDIR /home/tenshi

# -------------------------------------------------------------
# Set the container entrypoint.
ENTRYPOINT ["/tenshi/config/entrypoint.sh"]
