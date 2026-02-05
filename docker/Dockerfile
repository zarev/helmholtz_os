FROM osrf/ros:jazzy-desktop

SHELL ["/bin/bash", "-lc"]

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy

# ---------- Base tools & ROS packages ----------
RUN apt-get update && apt-get install -y \
    git curl wget \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    build-essential \
    sudo \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-moveit \
    ros-jazzy-ur-simulation-gz \
    ros-jazzy-ur-robot-driver \
    && rm -rf /var/lib/apt/lists/*

# ---------- rosdep ----------
RUN rosdep init || true && rosdep update

# ---------- Create non-root user with sudo ----------
ARG USERNAME=ubuntu
ARG USER_ID=1000
ARG GROUP_ID=1000

RUN set -eux; \
    # Resolve existing group name for GROUP_ID, or create one
    EXISTING_GROUP="$(getent group | awk -F: -v gid="${GROUP_ID}" '$3==gid {print $1; exit}')"; \
    if [ -n "${EXISTING_GROUP}" ]; then \
        GROUP_NAME="${EXISTING_GROUP}"; \
    else \
        groupadd --gid "${GROUP_ID}" "${USERNAME}"; \
        GROUP_NAME="${USERNAME}"; \
    fi; \
    \
    # If USER_ID already exists, reuse that user instead of forcing UID
    EXISTING_USER="$(getent passwd | awk -F: -v uid="${USER_ID}" '$3==uid {print $1; exit}')"; \
    if [ -n "${EXISTING_USER}" ]; then \
        USER_NAME="${EXISTING_USER}"; \
    else \
        USER_NAME="${USERNAME}"; \
    fi; \
    \
    # Ensure the desired username exists (create it only if it doesn't)
    if ! id -u "${USERNAME}" >/dev/null 2>&1; then \
        if [ "${USER_NAME}" = "${USERNAME}" ]; then \
            useradd --uid "${USER_ID}" --gid "${GROUP_ID}" -m "${USERNAME}"; \
        else \
            # UID is taken; create USERNAME without specifying UID, but with the desired GID
            useradd --gid "${GROUP_ID}" -m "${USERNAME}"; \
        fi; \
    fi; \
    \
    echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/${USERNAME}"; \
    chmod 0440 "/etc/sudoers.d/${USERNAME}"; \
    \
    touch "/home/${USERNAME}/.bashrc"; \
    echo "source /opt/ros/jazzy/setup.bash" >> "/home/${USERNAME}/.bashrc"; \
    chown -R "${USERNAME}:${GROUP_ID}" "/home/${USERNAME}"


WORKDIR /ws

# ---------- Switch to user ----------
USER ${USERNAME}
