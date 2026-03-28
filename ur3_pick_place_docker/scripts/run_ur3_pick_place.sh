#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash

USE_WS_OVERLAY="${USE_WS_OVERLAY:-0}"
UR_TYPE="${UR_TYPE:-ur3}"
REQUIRE_GUI="${REQUIRE_GUI:-1}"
RUN_PICK_PLACE_CLIENT="${RUN_PICK_PLACE_CLIENT:-1}"
LAUNCH_RVIZ="${LAUNCH_RVIZ:-0}"
ARM_ACTION_NAME="${ARM_ACTION_NAME:-/scaled_joint_trajectory_controller/follow_joint_trajectory}"
REQUIRE_GRIPPER="${REQUIRE_GRIPPER:-1}"
SIM_BACKEND="${SIM_BACKEND:-upstream}"
DISPLAY_SESSION="${XDG_SESSION_TYPE:-unknown}"

action_server_available() {
  local action_name="$1"
  ros2 action info "${action_name}" 2>/dev/null | grep -Eq '^Action servers: [1-9][0-9]*$'
}

wait_for_action_server() {
  local action_name="$1"
  local timeout_seconds="$2"
  local label="$3"
  local found=0

  echo "[run] Waiting for ${action_name} action server"
  for _ in $(seq 1 "${timeout_seconds}"); do
    if ! kill -0 "${SIM_PID}" >/dev/null 2>&1; then
      echo "[run] ERROR: simulation launch exited before ${action_name} became available" >&2
      echo "[run] Last launch log lines:" >&2
      tail -n 80 /tmp/ur_sim_control.log >&2 || true
      exit 1
    fi

    if ! kill -0 "${MOVEIT_PID}" >/dev/null 2>&1; then
      echo "[run] ERROR: move_group launch exited before ${action_name} became available" >&2
      echo "[run] Last move_group log lines:" >&2
      tail -n 80 /tmp/move_group.log >&2 || true
      exit 1
    fi

    if action_server_available "${action_name}"; then
      echo "[run] ${label} is available"
      found=1
      break
    fi
    sleep 1
  done

  if [ "${found}" != "1" ]; then
    echo "[run] ERROR: ${action_name} did not appear within timeout" >&2
    echo "[run] Check /tmp/ur_sim_control.log for details" >&2
    exit 1
  fi
}

activate_controller_with_retry() {
  local controller_name="$1"
  local spawner_log="/tmp/${controller_name}_spawner.log"

  echo "[run] Activating ${controller_name} with extended switch timeout"
  if ! ros2 run controller_manager spawner "${controller_name}" \
    -c /controller_manager \
    --controller-manager-timeout 120 \
    --service-call-timeout 120 \
    --switch-timeout 120 \
    > "${spawner_log}" 2>&1; then
    if grep -Eq "active' state|already active|already loaded, skipping load_controller" "${spawner_log}"; then
      echo "[run] ${controller_name} is already present; deferring readiness check to action/server availability"
      return 0
    fi

    echo "[run] ERROR: failed to activate ${controller_name}" >&2
    tail -n 80 "${spawner_log}" >&2 || true
    exit 1
  fi
}

if [ "${USE_WS_OVERLAY}" = "1" ] && [ -f /ws/install/setup.bash ]; then
  source /ws/install/setup.bash
fi

echo "[run] Detected host display session: ${DISPLAY_SESSION}"
if [ "${DISPLAY_SESSION}" = "wayland" ]; then
  echo "[run] Wayland session detected. Gazebo/RViz use XWayland via DISPLAY=${DISPLAY:-unset}."
fi

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

# If WORLD_FILE comes from a source tree, include its sibling models directory so
# model:// URIs referenced by the world can be resolved without an overlay build.
world_dir="$(dirname "${WORLD_FILE}")"
models_dir="$(dirname "${world_dir}")/models"
if [ -d "${models_dir}" ]; then
  export GZ_SIM_RESOURCE_PATH="${models_dir}:${world_dir}:${GZ_SIM_RESOURCE_PATH:-}"
  export IGN_GAZEBO_RESOURCE_PATH="${models_dir}:${world_dir}:${IGN_GAZEBO_RESOURCE_PATH:-}"
fi

# Support project-level worlds mounted outside the ROS source tree while their
# companion models remain in the workspace source tree.
workspace_models_dir="/ws/src/UR3_ROS2_PICK_AND_PLACE/ur_gazebo/models"
if [ -d "${workspace_models_dir}" ]; then
  export GZ_SIM_RESOURCE_PATH="${workspace_models_dir}:${GZ_SIM_RESOURCE_PATH:-}"
  export IGN_GAZEBO_RESOURCE_PATH="${workspace_models_dir}:${IGN_GAZEBO_RESOURCE_PATH:-}"
fi

# Allow model://<package_name>/... assets to resolve directly from the
# checked-in workspace source tree when those packages are not installed.
workspace_source_root="/ws/src/UR3_ROS2_PICK_AND_PLACE"
if [ -d "${workspace_source_root}" ]; then
  export GZ_SIM_RESOURCE_PATH="${workspace_source_root}:${GZ_SIM_RESOURCE_PATH:-}"
  export IGN_GAZEBO_RESOURCE_PATH="${workspace_source_root}:${IGN_GAZEBO_RESOURCE_PATH:-}"
fi

# Prefer repo-owned model overrides when present so they win over vendored
# workspace models with the same model:// name.
project_models_dir="/project_models"
if [ -d "${project_models_dir}" ]; then
  export GZ_SIM_RESOURCE_PATH="${project_models_dir}:${GZ_SIM_RESOURCE_PATH:-}"
  export IGN_GAZEBO_RESOURCE_PATH="${project_models_dir}:${IGN_GAZEBO_RESOURCE_PATH:-}"
fi

if [ "${REQUIRE_GUI}" = "1" ]; then
  if [ -z "${DISPLAY:-}" ]; then
    echo "[run] ERROR: DISPLAY is not set but REQUIRE_GUI=1" >&2
    if [ "${DISPLAY_SESSION}" = "wayland" ]; then
      echo "[run] Host fix (Wayland): ensure XWayland is available and DISPLAY is exported (commonly :0 or :1)" >&2
      echo "[run] Also allow local docker access: xhost +local:root" >&2
    else
      echo "[run] Host fix (X11): export DISPLAY=:0 and allow X11 access for docker" >&2
      echo "[run] Example: xhost +local:root" >&2
    fi
    exit 1
  fi

  if [ ! -S /tmp/.X11-unix/X0 ] && [ ! -S "/tmp/.X11-unix/X${DISPLAY#:}" ]; then
    echo "[run] ERROR: X11 socket not found in container (/tmp/.X11-unix)" >&2
    echo "[run] Ensure /tmp/.X11-unix is mounted and DISPLAY points to a valid host display" >&2
    exit 1
  fi

  if [ -n "${XAUTHORITY:-}" ] && [ ! -f "${XAUTHORITY}" ]; then
    echo "[run] WARNING: XAUTHORITY is set to ${XAUTHORITY} but file does not exist in container" >&2
    echo "[run] GUI may fail with authorization errors. Ensure host ~/.Xauthority is available." >&2
  fi

  if [ "${DISPLAY_SESSION}" = "wayland" ]; then
    if [ -z "${XAUTHORITY:-}" ]; then
      echo "[run] WARNING: XAUTHORITY is not set. If GUI fails with authorization errors, run: xhost +local:root" >&2
    fi
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
  upstream_extra_args=()
  if [ "${REQUIRE_GRIPPER}" = "1" ]; then
    gripper_description_file="/ws/config/ur_gz_robotiq.urdf.xacro"
    gripper_controllers_file="/ws/src/UR3_ROS2_PICK_AND_PLACE/moveit_config/config/ros2_controllers.yaml"

    if [ -f "${gripper_description_file}" ] && [ -f "${gripper_controllers_file}" ]; then
      echo "[run] REQUIRE_GRIPPER=1; launching upstream sim with repo-owned gripper description/controllers"
      upstream_extra_args+=("description_file:=${gripper_description_file}")
      upstream_extra_args+=("controllers_file:=${gripper_controllers_file}")
      upstream_extra_args+=("initial_joint_controller:=arm_controller")
      if [ "${ARM_ACTION_NAME}" = "/scaled_joint_trajectory_controller/follow_joint_trajectory" ]; then
        ARM_ACTION_NAME="/arm_controller/follow_joint_trajectory"
      fi
    else
      echo "[run] WARNING: gripper config files not found for upstream launch; gripper action may be unavailable" >&2
    fi
  fi

  echo "[run] Launching upstream UR simulation for ${UR_TYPE} (world_file=${WORLD_FILE})"
  ros2 launch ur_simulation_gz ur_sim_control.launch.py ur_type:="${UR_TYPE}" launch_rviz:=false world_file:="${WORLD_FILE}" "${upstream_extra_args[@]}" > /tmp/ur_sim_control.log 2>&1 &
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

if [ "${SIM_BACKEND}" = "upstream" ]; then
  activate_controller_with_retry "arm_controller"
fi

wait_for_action_server "${ARM_ACTION_NAME}" 120 "${ARM_ACTION_NAME}"

if [ "${REQUIRE_GRIPPER}" = "1" ] && [ "${SIM_BACKEND}" = "upstream" ]; then
  activate_controller_with_retry "gripper_controller"
fi

if [ "${REQUIRE_GRIPPER}" = "1" ]; then
  wait_for_action_server "/gripper_controller/gripper_cmd" 120 "/gripper_controller/gripper_cmd"
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