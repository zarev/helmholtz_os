FROM osrf/ros:jazzy-desktop

ARG DEBIAN_FRONTEND=noninteractive
ARG REPO_URL="https://github.com/darshmenon/UR3_ROS2_PICK_AND_PLACE.git"
ARG REPO_BRANCH="main"

SHELL ["/bin/bash", "-lc"]

# Basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    python3-pip \
    python3-rosdep \
    python3-colcon-common-extensions \
    python3-vcstool \
    xauth \
    && rm -rf /var/lib/apt/lists/*

# Packages explicitly listed in the repo README (simulation stack)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-rviz2 \
    ros-jazzy-joint-state-publisher \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-controller-manager \
    ros-jazzy-joint-trajectory-controller \
    ros-jazzy-position-controllers \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-ros2controlcli \
    ros-jazzy-ros-gz \
    && rm -rf /var/lib/apt/lists/*

ENV WS=/ws
RUN mkdir -p ${WS}/src
WORKDIR ${WS}/src

# Clone project
RUN git clone --branch ${REPO_BRANCH} --depth 1 ${REPO_URL} ur3_pick_place

WORKDIR ${WS}

RUN source /opt/ros/jazzy/setup.bash && \
    rosdep install --from-paths src --ignore-src -r -y \
      --skip-keys="\
moveit_core moveit_msgs moveit_common \
moveit_ros_planning moveit_ros_planning_interface moveit_ros_move_group moveit_ros_visualization \
moveit_visual_tools moveit_kinematics moveit_simple_controller_manager moveit_setup_assistant \
moveit_planners moveit_configs_utils \
moveit_resources_panda_moveit_config moveit_resources_fanuc_moveit_config \
moveit_ros_warehouse warehouse_ros warehouse_ros_sqlite \
pcl_ros py_binding_tools \
gz_ros2_control_demos \
libmongoclient-dev liburdfdom-tools joint_state_publisher_gui"


# Make shells auto-source the overlay
RUN echo "source /opt/ros/jazzy/setup.bash" >> /etc/bash.bashrc && \
    echo "source /ws/install/setup.bash" >> /etc/bash.bashrc

WORKDIR /ws
CMD ["bash"]
