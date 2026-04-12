# syntax=docker/dockerfile:1.7

ARG ROS_DISTRO=jazzy
FROM osrf/ros:${ROS_DISTRO}-desktop-full

ARG ROS_DISTRO
ARG GZ_VERSION=harmonic
ARG USERNAME=developer
ARG USER_UID=1000
ARG USER_GID=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV ROS_DISTRO=${ROS_DISTRO}
ENV GZ_VERSION=${GZ_VERSION}
ENV ROS_WS=/workspaces/moxynova_ws
ENV COLCON_HOME=/home/${USERNAME}/.colcon
ENV UR_TYPE=ur3e
ENV UR_DESCRIPTION_FILE=${ROS_WS}/src/lab_robot_description/urdf/ur_with_robotiq_2f_85.urdf.xacro
ENV PICK_PLACE_WORLD_FILE=${ROS_WS}/src/lab_robot_gazebo/worlds/pick_and_place_demo.world
ENV ARM_TRAJECTORY_ACTION=/scaled_joint_trajectory_controller/follow_joint_trajectory
ENV MOVEIT_PLANNING_GROUP=ur_manipulator
ENV LAUNCH_RVIZ=false
ENV ROS_DOMAIN_ID=42

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
    && curl -fsSL https://packages.osrfoundation.org/gazebo.gpg \
        | gpg --dearmor -o /usr/share/keyrings/gazebo-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/gazebo-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(. /etc/os-release && echo "${UBUNTU_CODENAME}") main" \
        > /etc/apt/sources.list.d/gazebo-stable.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        bash-completion \
        build-essential \
        cmake \
        gdb \
        git \
        gosu \
        iputils-ping \
        dbus-x11 \
        libgl1-mesa-dri \
        libgl1 \
        libglu1-mesa \
        libx11-6 \
        libxcursor1 \
        libxext6 \
        libxi6 \
        libxinerama1 \
        libxrandr2 \
        mesa-utils \
        nano \
        python3-argcomplete \
        python3-colcon-common-extensions \
        python3-dev \
        python3-numpy \
        python3-opencv \
        python3-pil \
        python3-pil.imagetk \
        python3-pip \
        python3-rosdep \
        python3-scipy \
        python3-tk \
        python3-transforms3d \
        python3-venv \
        python3-vcstool \
        python3-yaml \
        sudo \
        wget \
        x11-apps \
        gz-${GZ_VERSION} \
        ros-${ROS_DISTRO}-controller-manager \
        ros-${ROS_DISTRO}-gripper-controllers \
        ros-${ROS_DISTRO}-gz-ros2-control \
        ros-${ROS_DISTRO}-image-geometry \
        ros-${ROS_DISTRO}-image-transport \
        ros-${ROS_DISTRO}-joint-state-broadcaster \
        ros-${ROS_DISTRO}-joint-state-publisher \
        ros-${ROS_DISTRO}-joint-state-publisher-gui \
        ros-${ROS_DISTRO}-joint-trajectory-controller \
        ros-${ROS_DISTRO}-moveit \
        ros-${ROS_DISTRO}-moveit-msgs \
        ros-${ROS_DISTRO}-moveit-py \
        ros-${ROS_DISTRO}-moveit-servo \
        ros-${ROS_DISTRO}-moveit-task-constructor-capabilities \
        ros-${ROS_DISTRO}-moveit-task-constructor-core \
        ros-${ROS_DISTRO}-moveit-task-constructor-demo \
        ros-${ROS_DISTRO}-moveit-task-constructor-msgs \
        ros-${ROS_DISTRO}-moveit-task-constructor-visualization \
        ros-${ROS_DISTRO}-moveit-visual-tools \
        ros-${ROS_DISTRO}-pcl-ros \
        ros-${ROS_DISTRO}-pilz-industrial-motion-planner \
        ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
        ros-${ROS_DISTRO}-robot-state-publisher \
        ros-${ROS_DISTRO}-robotiq-description \
        ros-${ROS_DISTRO}-ros-gz \
        ros-${ROS_DISTRO}-ros-gz-bridge \
        ros-${ROS_DISTRO}-ros-gz-sim \
        ros-${ROS_DISTRO}-tf-transformations \
        ros-${ROS_DISTRO}-tf2-geometry-msgs \
        ros-${ROS_DISTRO}-tf2-tools \
        ros-${ROS_DISTRO}-ur \
        ros-${ROS_DISTRO}-ur-description \
        ros-${ROS_DISTRO}-ur-moveit-config \
        ros-${ROS_DISTRO}-ur-robot-driver \
        ros-${ROS_DISTRO}-ur-simulation-gz \
        ros-${ROS_DISTRO}-vision-msgs \
        ros-${ROS_DISTRO}-vision-opencv \
        ros-${ROS_DISTRO}-xacro \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/from launch_ros.actions import Node/from launch_ros.actions import Node\nfrom launch_ros.parameter_descriptions import ParameterValue/' /opt/ros/${ROS_DISTRO}/share/ur_simulation_gz/launch/ur_sim_control.launch.py \
    && sed -i 's/robot_description = {"robot_description": robot_description_content}/robot_description = {"robot_description": ParameterValue(robot_description_content, value_type=str)}/' /opt/ros/${ROS_DISTRO}/share/ur_simulation_gz/launch/ur_sim_control.launch.py

RUN rosdep init 2>/dev/null || true \
    && rosdep update --rosdistro ${ROS_DISTRO}

RUN if getent group ${USERNAME} >/dev/null 2>&1; then \
        groupmod -o --gid ${USER_GID} ${USERNAME}; \
    else \
        groupadd -o --gid ${USER_GID} ${USERNAME}; \
    fi \
    && if id -u ${USERNAME} >/dev/null 2>&1; then \
        usermod -o --uid ${USER_UID} --gid ${USER_GID} --home /home/${USERNAME} --shell /bin/bash ${USERNAME}; \
    else \
        useradd -o --uid ${USER_UID} --gid ${USER_GID} --create-home --shell /bin/bash ${USERNAME}; \
    fi \
    && usermod -aG sudo,video,audio ${USERNAME} \
    && echo "${USERNAME} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME} \
    && mkdir -p ${ROS_WS}/src ${ROS_WS}/build ${ROS_WS}/install ${ROS_WS}/log /home/${USERNAME}/.ros \
    && chown -R ${USERNAME}:${USERNAME} ${ROS_WS} /home/${USERNAME}

COPY docker/entrypoint.sh /usr/local/bin/moxynova-entrypoint.sh
COPY docker/run_pick_place_demo.sh /usr/local/bin/moxynova-pick-place-demo.sh
COPY --chown=${USERNAME}:${USERNAME} src ${ROS_WS}/src

RUN chmod +x /usr/local/bin/moxynova-entrypoint.sh \
    && chmod +x /usr/local/bin/moxynova-pick-place-demo.sh \
    && echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /etc/bash.bashrc \
    && echo "if [ -f ${ROS_WS}/install/setup.bash ]; then source ${ROS_WS}/install/setup.bash; fi" >> /etc/bash.bashrc \
    && echo "if [ -f /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash ]; then source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash; fi" >> /etc/bash.bashrc \
    && source /opt/ros/${ROS_DISTRO}/setup.bash \
    && colcon --log-base ${ROS_WS}/log build \
        --symlink-install \
        --base-paths ${ROS_WS}/src \
        --build-base ${ROS_WS}/build \
        --install-base ${ROS_WS}/install

WORKDIR ${ROS_WS}

ENTRYPOINT ["/usr/local/bin/moxynova-entrypoint.sh"]
CMD ["/usr/local/bin/moxynova-pick-place-demo.sh"]
