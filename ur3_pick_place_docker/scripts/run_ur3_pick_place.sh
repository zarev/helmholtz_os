#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash

USE_WS_OVERLAY="${USE_WS_OVERLAY:-0}"
if [ "${USE_WS_OVERLAY}" = "1" ] && [ -f /ws/install/setup.bash ]; then
  source /ws/install/setup.bash
fi

UR_TYPE="${UR_TYPE:-ur3}"
REQUIRE_GUI="${REQUIRE_GUI:-1}"
RUN_PICK_PLACE_CLIENT="${RUN_PICK_PLACE_CLIENT:-1}"
LAUNCH_RVIZ="${LAUNCH_RVIZ:-0}"
ARM_ACTION_NAME="${ARM_ACTION_NAME:-/scaled_joint_trajectory_controller/follow_joint_trajectory}"
REQUIRE_GRIPPER="${REQUIRE_GRIPPER:-0}"
SIM_BACKEND="${SIM_BACKEND:-upstream}"

if [ -n "${WORLD_FILE:-}" ]; then
  if [ ! -f "${WORLD_FILE}" ] && [ "${WORLD_FILE}" != "empty.sdf" ]; then
    echo "[run] WARNING: WORLD_FILE not found at ${WORLD_FILE}, falling back to empty.sdf" >&2
    WORLD_FILE="empty.sdf"
  fi
else
  # Prefer custom world only when explicitly using the workspace overlay.
  if [ "${USE_WS_OVERLAY}" = "1" ] && [ -f "/ws/install/ur_gazebo/share/ur_gazebo/worlds/pick_and_place_demo.world" ]; then
    WORLD_FILE="/ws/install/ur_gazebo/share/ur_gazebo/worlds/pick_and_place_demo.world"
  elif [ -f "/opt/ros/jazzy/share/ur_gazebo/worlds/pick_and_place_demo.world" ]; then
    WORLD_FILE="/opt/ros/jazzy/share/ur_gazebo/worlds/pick_and_place_demo.world"
  else
    WORLD_FILE="empty.sdf"
  fi
fi

if [ "${REQUIRE_GUI}" = "1" ]; then
  if [ -z "${DISPLAY:-}" ]; then
    echo "[run] ERROR: DISPLAY is not set but REQUIRE_GUI=1" >&2
    echo "[run] Host fix: export DISPLAY=:0 and allow X11 access for docker" >&2
    echo "[run] Example: xhost +local:root" >&2
    exit 1
  fi

  if [ ! -S /tmp/.X11-unix/X0 ] && [ ! -S "/tmp/.X11-unix/X${DISPLAY#:}" ]; then
    echo "[run] ERROR: X11 socket not found in container (/tmp/.X11-unix)" >&2
    echo "[run] Ensure /tmp/.X11-unix is mounted and DISPLAY points to a valid host display" >&2
    exit 1
  fi
fi

if [ "${SIM_BACKEND}" = "overlay_gazebo" ]; then
  if [ "${USE_WS_OVERLAY}" != "1" ]; then
    echo "[run] ERROR: SIM_BACKEND=overlay_gazebo requires USE_WS_OVERLAY=1" >&2
    exit 1
  fi
  if ! ros2 pkg prefix ur_gazebo >/dev/null 2>&1; then
    echo "[run] ERROR: ur_gazebo package not found in current environment" >&2
    exit 1
  fi
  echo "[run] Launching overlay UR Gazebo for ${UR_TYPE} (world_file=${WORLD_FILE})"
  ros2 launch ur_gazebo ur.gazebo.launch.py ur_type:="${UR_TYPE}" use_sim_time:=true world_file:="${WORLD_FILE}" > /tmp/ur_sim_control.log 2>&1 &
  SIM_PID=$!
else
  echo "[run] Launching upstream UR simulation for ${UR_TYPE} (world_file=${WORLD_FILE})"
  ros2 launch ur_simulation_gz ur_sim_control.launch.py ur_type:="${UR_TYPE}" launch_rviz:=false world_file:="${WORLD_FILE}" > /tmp/ur_sim_control.log 2>&1 &
  SIM_PID=$!
fi

if [ "${LAUNCH_RVIZ}" = "1" ]; then
  MOVEIT_LAUNCH_RVIZ=true
else
  MOVEIT_LAUNCH_RVIZ=false
fi

echo "[run] Launching upstream MoveIt"
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:="${UR_TYPE}" use_sim_time:=true launch_rviz:="${MOVEIT_LAUNCH_RVIZ}" > /tmp/move_group.log 2>&1 &
MOVEIT_PID=$!

cleanup() {
  if kill -0 "${MOVEIT_PID}" >/dev/null 2>&1; then
    kill "${MOVEIT_PID}" >/dev/null 2>&1 || true
  fi
  if kill -0 "${SIM_PID}" >/dev/null 2>&1; then
    kill "${SIM_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "[run] Waiting for ${ARM_ACTION_NAME} action server"
found_arm_action=0
for i in $(seq 1 120); do
  if ! kill -0 "${SIM_PID}" >/dev/null 2>&1; then
    echo "[run] ERROR: simulation launch exited before arm action became available" >&2
    echo "[run] Last launch log lines:" >&2
    tail -n 80 /tmp/ur_sim_control.log >&2 || true
    exit 1
  fi

  if ! kill -0 "${MOVEIT_PID}" >/dev/null 2>&1; then
    echo "[run] ERROR: move_group launch exited before arm action became available" >&2
    echo "[run] Last move_group log lines:" >&2
    tail -n 80 /tmp/move_group.log >&2 || true
    exit 1
  fi

  if ros2 action list 2>/dev/null | grep -q "^${ARM_ACTION_NAME}$"; then
    echo "[run] ${ARM_ACTION_NAME} is available"
    found_arm_action=1
    break
  fi
  sleep 1
done

if [ "${found_arm_action}" != "1" ]; then
  echo "[run] ERROR: ${ARM_ACTION_NAME} did not appear within timeout" >&2
  echo "[run] Check /tmp/ur_sim_control.log for details" >&2
  exit 1
fi

echo "[run] Waiting for /compute_ik service"
found_compute_ik=0
for i in $(seq 1 120); do
  if ! kill -0 "${SIM_PID}" >/dev/null 2>&1; then
    echo "[run] ERROR: simulation launch exited before /compute_ik became available" >&2
    echo "[run] Last launch log lines:" >&2
    tail -n 80 /tmp/ur_sim_control.log >&2 || true
    exit 1
  fi

  if ! kill -0 "${MOVEIT_PID}" >/dev/null 2>&1; then
    echo "[run] ERROR: move_group launch exited before /compute_ik became available" >&2
    echo "[run] Last move_group log lines:" >&2
    tail -n 80 /tmp/move_group.log >&2 || true
    exit 1
  fi

  if ros2 service list 2>/dev/null | grep -q '^/compute_ik$'; then
    echo "[run] /compute_ik is available"
    found_compute_ik=1
    break
  fi
  sleep 1
done

if [ "${found_compute_ik}" != "1" ]; then
  echo "[run] ERROR: /compute_ik did not appear within timeout" >&2
  echo "[run] Check /tmp/move_group.log and /tmp/ur_sim_control.log for details" >&2
  exit 1
fi

if [ "${REQUIRE_GRIPPER}" = "1" ]; then
  echo "[run] Waiting for /gripper_controller/gripper_cmd action server"
  found_gripper_action=0
  for i in $(seq 1 120); do
    if ! kill -0 "${SIM_PID}" >/dev/null 2>&1; then
      echo "[run] ERROR: simulation launch exited before /gripper_controller/gripper_cmd became available" >&2
      echo "[run] Last launch log lines:" >&2
      tail -n 80 /tmp/ur_sim_control.log >&2 || true
      exit 1
    fi

    if ros2 action list 2>/dev/null | grep -q '^/gripper_controller/gripper_cmd$'; then
      echo "[run] /gripper_controller/gripper_cmd is available"
      found_gripper_action=1
      break
    fi
    sleep 1
  done

  if [ "${found_gripper_action}" != "1" ]; then
    echo "[run] ERROR: /gripper_controller/gripper_cmd did not appear within timeout" >&2
    echo "[run] Check /tmp/ur_sim_control.log for details" >&2
    exit 1
  fi
else
  echo "[run] REQUIRE_GRIPPER=${REQUIRE_GRIPPER}; skipping gripper action wait"
fi

if [ "${RUN_PICK_PLACE_CLIENT}" != "1" ]; then
  echo "[run] RUN_PICK_PLACE_CLIENT=${RUN_PICK_PLACE_CLIENT}, keeping container alive for external control"
  wait "${SIM_PID}" "${MOVEIT_PID}"
  exit $?
fi

echo "[run] Starting pick and place action client"
exec python3 /ws/pick_place_moveit_action.py