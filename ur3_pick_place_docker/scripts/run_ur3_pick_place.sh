#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/jazzy/setup.bash

if [ -f /ws/install/setup.bash ]; then
  source /ws/install/setup.bash
fi

UR_TYPE="${UR_TYPE:-ur3}"

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
  if ros2 action list 2>/dev/null | grep -q '^/move_action$'; then
    echo "[run] /move_action is available"
    break
  fi
  sleep 1
done

if ! ros2 action list 2>/dev/null | grep -q '^/move_action$'; then
  echo "[run] ERROR: /move_action did not appear within timeout" >&2
  echo "[run] Check /tmp/ur_sim_moveit.log for details" >&2
  exit 1
fi

echo "[run] Starting pick and place action client"
exec python3 /ws/pick_place_moveit_action.py