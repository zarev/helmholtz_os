FROM osrf/ros:jazzy-desktop

SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive

# Base tooling + rosdep/colcon
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget nano \
    python3-pip python3-venv \
    python3-rosdep \
    python3-colcon-common-extensions \
    build-essential cmake pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Common runtime helpers for GUI apps
RUN apt-get update && apt-get install -y --no-install-recommends \
    dbus-x11 x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep (safe if already initialized)
RUN rosdep init || true && rosdep update

# Workspace path
ENV WS=/ws
WORKDIR ${WS}

# Copy entrypoint (sources ROS + workspace overlay if present)
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
