#!/usr/bin/env bash
set -e

source /opt/ros/jazzy/setup.bash

if [ -f /ws/install/setup.bash ]; then
  source /ws/install/setup.bash
fi

add_gz_share () {
  local pkg="$1"
  local prefix
  local pkg_share
  prefix="$(ros2 pkg prefix "$pkg" 2>/dev/null || true)"
  if [ -n "$prefix" ]; then
    pkg_share="${prefix}/share/${pkg}"

    if [ -d "${pkg_share}/models" ]; then
      export GZ_SIM_RESOURCE_PATH="${pkg_share}/models:${GZ_SIM_RESOURCE_PATH}"
      export IGN_GAZEBO_RESOURCE_PATH="${pkg_share}/models:${IGN_GAZEBO_RESOURCE_PATH}"
    fi

    if [ -d "${pkg_share}" ]; then
      export GZ_SIM_RESOURCE_PATH="${pkg_share}:${GZ_SIM_RESOURCE_PATH}"
      export IGN_GAZEBO_RESOURCE_PATH="${pkg_share}:${IGN_GAZEBO_RESOURCE_PATH}"
    fi

    export GZ_SIM_RESOURCE_PATH="${prefix}/share:${GZ_SIM_RESOURCE_PATH}"
    export IGN_GAZEBO_RESOURCE_PATH="${prefix}/share:${IGN_GAZEBO_RESOURCE_PATH}"
  fi
}

# Any package referenced via model://<pkg_name>/...
add_gz_share ur_description
add_gz_share ur_simulation_gz
add_gz_share ur_gazebo
add_gz_share robotiq_2f_85_gripper_visualization
add_gz_share ur_moveit_config

exec "$@"
