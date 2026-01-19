FROM osrf/ros:jazzy-desktop

SHELL ["/bin/bash", "-lc"]

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=jazzy


# Base tools
RUN apt-get update && apt-get install -y \
    git curl wget \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    build-essential \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-moveit \
    ros-jazzy-ur-simulation-gz \
    ros-jazzy-ur-robot-driver \
    && rm -rf /var/lib/apt/lists/*


# rosdep init (safe if already initialized)
RUN rosdep init || true
RUN rosdep update

# MoveIt 2 (Jazzy packages)
RUN apt-get update && apt-get install -y \
    ros-jazzy-moveit \
    && rm -rf /var/lib/apt/lists/*

# Gazebo Harmonic integration + ros2_control plugin for gz-sim
# (gz_ros2_control is the standard bridge for ros2_control in Gazebo Sim) :contentReference[oaicite:7]{index=7}
RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-gz-ros2-control \
    && rm -rf /var/lib/apt/lists/*


RUN echo "source /opt/ros/jazzy/setup.bash" >> /root/.bashrc

WORKDIR /ws
