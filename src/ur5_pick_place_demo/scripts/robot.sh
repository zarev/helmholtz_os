#!/usr/bin/env bash
set -e

source /opt/ros/jazzy/setup.bash

# Build only your package if overlay not built yet
if [ ! -f /ws/install/setup.bash ]; then
  cd /ws
  colcon build --symlink-install --packages-select ur5_pick_place_demo
fi

source /ws/install/setup.bash

# UR5e simulation
ros2 launch ur_simulation_gz ur_sim_control.launch.py ur_type:=ur5e
