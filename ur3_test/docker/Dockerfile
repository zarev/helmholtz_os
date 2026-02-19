FROM osrf/ros:jazzy-desktop

ARG DEBIAN_FRONTEND=noninteractive
ARG ROS_DISTRO=jazzy

ARG UR_REPO_URL="https://github.com/darshmenon/UR3_ROS2_PICK_AND_PLACE.git"
ARG UR_REPO_BRANCH="main"
ENV UR_REPO_URL=${UR_REPO_URL}
ENV UR_REPO_BRANCH=${UR_REPO_BRANCH}

ARG USERNAME=ros
ARG USER_ID=1000
ARG GROUP_ID=1000
ENV UR_WS=/ws
ENV UR_SEED=/opt/ur3_seed

SHELL ["/bin/bash", "-lc"]

# -----------------------
# Base tools + common deps
# -----------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    build-essential cmake pkg-config \
    python3-pip \
    python3-rosdep \
    python3-vcstool \
    python3-colcon-common-extensions \
    python3-argcomplete \
    xauth \
    mesa-utils \
    libeigen3-dev \
    libboost-all-dev \
    libassimp-dev \
    libpoco-dev \
    libtinyxml2-dev \
    liburdfdom-dev \
    liburdfdom-tools \
    libsqlite3-dev \
    libyaml-cpp-dev \
    liboctomap-dev \
    libfmt-dev \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------
# ROS deps referenced by the UR3 repo README
# -----------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-${ROS_DISTRO}-rviz2 \
    ros-${ROS_DISTRO}-joint-state-publisher \
    ros-${ROS_DISTRO}-robot-state-publisher \
    ros-${ROS_DISTRO}-ros2-control \
    ros-${ROS_DISTRO}-ros2-controllers \
    ros-${ROS_DISTRO}-controller-manager \
    ros-${ROS_DISTRO}-joint-trajectory-controller \
    ros-${ROS_DISTRO}-position-controllers \
    ros-${ROS_DISTRO}-gz-ros2-control \
    ros-${ROS_DISTRO}-ros2controlcli \
    ros-${ROS_DISTRO}-ros-gz \
    ros-${ROS_DISTRO}-xacro \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends gosu && rm -rf /var/lib/apt/lists/*
COPY --chmod=755 entrypoint.sh /usr/local/bin/entrypoint.sh
COPY patches/ur.gazebo.launch.py /opt/ur3_patches/ur.gazebo.launch.py
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# -----------------------
# rosdep init/update
# -----------------------
RUN rosdep init 2>/dev/null || true && rosdep update


# -----------------------
# Seed UR3 repo for runtime workspace bootstrapping
# -----------------------
RUN mkdir -p ${UR_SEED}/src
WORKDIR ${UR_SEED}/src

RUN git clone --branch ${UR_REPO_BRANCH} --depth 1 ${UR_REPO_URL} UR3_ROS2_PICK_AND_PLACE

RUN if [ -f /opt/ur3_patches/ur.gazebo.launch.py ]; then \
    cp /opt/ur3_patches/ur.gazebo.launch.py \
    ${UR_SEED}/src/UR3_ROS2_PICK_AND_PLACE/ur_gazebo/launch/ur.gazebo.launch.py; \
    fi

RUN apt-get update && \
    source /opt/ros/${ROS_DISTRO}/setup.bash && \
    rosdep install --from-paths ${UR_SEED}/src --ignore-src -r -y --rosdistro ${ROS_DISTRO} && \
    rm -rf /var/lib/apt/lists/*


# -----------------------
# Auto-source for interactive shells
# -----------------------
RUN echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /etc/bash.bashrc && \
    echo "source /ws/install/setup.bash" >> /etc/bash.bashrc

# Default to non-root at runtime
WORKDIR /ws

CMD ["bash", "-lc", "echo '[ur3 container] ready'; sleep infinity"]

RUN export MAKEFLAGS="-j0" && \
    source /opt/ros/jazzy/setup.bash && \
    colcon build --symlink-install