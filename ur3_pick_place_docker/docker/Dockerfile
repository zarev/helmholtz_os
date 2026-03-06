FROM ros:jazzy

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive

# Install base tools
RUN apt-get update && apt-get install -y \
    git \
    curl \
    wget \
    nano \
    build-essential \
    cmake \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    && rm -rf /var/lib/apt/lists/*

# Initialize rosdep
RUN rosdep init || true && rosdep update

# Install ROS packages
RUN apt-get update && apt-get install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-sim \
    ros-jazzy-moveit \
    ros-jazzy-moveit-visual-tools \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-tf2-tools \
    ros-jazzy-test-msgs \
    ros-jazzy-py-binding-tools \
    && rm -rf /var/lib/apt/lists/*

# Workspace
WORKDIR /ws
RUN mkdir -p src

# Clone repo and remove unwanted packages in ONE layer
RUN cd src && \
    git clone https://github.com/darshmenon/UR3_ROS2_PICK_AND_PLACE.git && \
    rm -rf \
      UR3_ROS2_PICK_AND_PLACE/ur_system_tests \
      UR3_ROS2_PICK_AND_PLACE/ur_mtc_pick_place_demo \
      UR3_ROS2_PICK_AND_PLACE/ur_mtc_demos \
      UR3_ROS2_PICK_AND_PLACE/ur_moveit_demos \
      UR3_ROS2_PICK_AND_PLACE/src/moveit_task_constructor \
      UR3_ROS2_PICK_AND_PLACE/src/warehouse_ros_mongo

# Build workspace
RUN source /opt/ros/jazzy/setup.bash && \
    rosdep install --from-paths src --ignore-src -r -y && \
    colcon build

# Auto source ROS
RUN echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc && \
    echo "source /ws/install/setup.bash" >> ~/.bashrc

WORKDIR /ws

CMD ["bash"]