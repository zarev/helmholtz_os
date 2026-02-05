ARG ROS_DISTRO=jazzy
FROM ros:${ROS_DISTRO}-ros-base

ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=${USER_UID}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    sudo curl git \
    python3-pip python3-colcon-common-extensions python3-rosdep python3-vcstool \
    ros-${ROS_DISTRO}-demo-nodes-py \
 && rm -rf /var/lib/apt/lists/*

# Create a matching non-root user
RUN if id -u ${USER_UID} >/dev/null 2>&1; then userdel $(id -un ${USER_UID}); fi || true \
 && groupadd --gid ${USER_GID} ${USERNAME} \
 && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} \
 && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
 && chmod 0440 /etc/sudoers.d/${USERNAME}

RUN rosdep init 2>/dev/null || true

ENV SHELL=/bin/bash
USER ${USERNAME}
WORKDIR /workspaces/helmholtz_os
CMD ["/bin/bash"]
