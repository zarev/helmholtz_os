#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash

if [ -f /ws/install/setup.bash ]; then
  source /ws/install/setup.bash
fi

UR_TYPE="${UR_TYPE:-ur3}"
REQUIRE_GUI="${REQUIRE_GUI:-1}"
RUN_PICK_PLACE_CLIENT="${RUN_PICK_PLACE_CLIENT:-1}"

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

echo "[run] Launching UR simulation + MoveIt for ${UR_TYPE}"
ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:="${UR_TYPE}" > /tmp/ur_sim_moveit.log 2>&1 &
LAUNCH_PID=$!

cleanup() {
  if kill -0 "${LAUNCH_PID}" >/dev/null 2>&1; then
    kill "${LAUNCH_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

echo "[run] Waiting for /move_action action server"
for i in $(seq 1 120); do
  if ! kill -0 "${LAUNCH_PID}" >/dev/null 2>&1; then
    echo "[run] ERROR: launch process exited before /move_action became available" >&2
    echo "[run] Last launch log lines:" >&2
    tail -n 60 /tmp/ur_sim_moveit.log >&2 || true
    exit 1
  fi

  if ros2 action list 2>/dev/null | grep -q '^/move_action$'; then
    echo "[run] /move_action is available"
    break
  fi
  sleep 1
done

if ! ros2 action list 2>/dev/null | grep -q '^/move_action$'; then
  echo "[run] ERROR: /move_action did not appear within timeout" >&2
  echo "[run] Check /tmp/ur_sim_moveit.log for details (look for Qt/X11 display errors)" >&2
  exit 1
fi

if [ "${RUN_PICK_PLACE_CLIENT}" != "1" ]; then
  echo "[run] RUN_PICK_PLACE_CLIENT=${RUN_PICK_PLACE_CLIENT}, keeping container alive for external control"
  wait "${LAUNCH_PID}"
  exit $?
fi

echo "[run] Starting pick and place action client"
exec python3 /ws/pick_place_moveit_action.py