#!/usr/bin/env bash
set -euo pipefail

TERMINAL_CMD="${TERMINAL_CMD:-}"

if [[ -z "$TERMINAL_CMD" ]]; then
  if command -v gnome-terminal >/dev/null 2>&1; then
    TERMINAL_CMD="gnome-terminal"
  elif command -v konsole >/dev/null 2>&1; then
    TERMINAL_CMD="konsole"
  elif command -v xterm >/dev/null 2>&1; then
    TERMINAL_CMD="xterm"
  else
    echo "No supported terminal emulator found (gnome-terminal, konsole, xterm)." >&2
    echo "Set TERMINAL_CMD to your terminal, or run commands manually." >&2
    exit 1
  fi
fi

ROS_SETUP="${ROS_SETUP:-}"
PREFIX=""
if [[ -n "$ROS_SETUP" ]]; then
  PREFIX="source \"$ROS_SETUP\" && "
fi

UR_TYPE="${UR_TYPE:-ur3}"
CMD1="ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=${UR_TYPE}"
CMD2='python3 /ws/pick_place_moveit_action.py'
CMD3='tail -f /tmp/pick_place_moveit_action.log'

SLEEP_BETWEEN="${SLEEP_BETWEEN:-2}"
SET_GAZEBO_CAMERA="${SET_GAZEBO_CAMERA:-1}"
CAMERA_WAIT_TIMEOUT="${CAMERA_WAIT_TIMEOUT:-45}"
# Side-profile default: battery/cylinder on left and UR3 on right at startup.
DEFAULT_GAZEBO_CAMERA_REQ='pose: { position: { x: 2.45 y: -1.35 z: 1.25 } orientation: { x: -0.12 y: 0.33 z: 0.89 w: 0.28 } }'
GAZEBO_CAMERA_REQ="${GAZEBO_CAMERA_REQ:-${DEFAULT_GAZEBO_CAMERA_REQ}}"

run_in_terminal() {
  local cmd="$1"
  case "$TERMINAL_CMD" in
    gnome-terminal)
      gnome-terminal -- bash -lc "$cmd; exec bash"
      ;;
    konsole)
      konsole --hold -e bash -lc "$cmd"
      ;;
    xterm)
      xterm -hold -e bash -lc "$cmd"
      ;;
    *)
      "$TERMINAL_CMD" -e bash -lc "$cmd"
      ;;
  esac
}

set_gazebo_camera() {
  local -i timeout_s="$1"
  local req="$2"

  if ! command -v gz >/dev/null 2>&1; then
    echo "[camera] gz CLI not found; skipping camera setup." >&2
    return 0
  fi

  echo "[camera] Waiting for /gui/move_to/pose service (timeout ${timeout_s}s)..."
  local -i waited=0
  until gz service -l 2>/dev/null | grep -q '^/gui/move_to/pose$'; do
    sleep 1
    waited=$((waited + 1))
    if (( waited >= timeout_s )); then
      echo "[camera] Timeout waiting for /gui/move_to/pose; skipping camera setup." >&2
      return 0
    fi
  done

  echo "[camera] Applying startup camera pose."
  gz service -s /gui/move_to/pose \
    --reqtype gz.msgs.GUICamera \
    --reptype gz.msgs.Boolean \
    --timeout 5000 \
    --req "$req" || echo "[camera] Failed to apply camera pose." >&2
}

run_in_terminal "${PREFIX}${CMD1}"

if [[ "$SET_GAZEBO_CAMERA" == "1" ]]; then
  (
    if [[ -n "$ROS_SETUP" ]]; then
      # shellcheck disable=SC1090
      source "$ROS_SETUP"
    fi
    set_gazebo_camera "$CAMERA_WAIT_TIMEOUT" "$GAZEBO_CAMERA_REQ"
  ) &
fi

sleep "$SLEEP_BETWEEN"
run_in_terminal "${PREFIX}${CMD2}"
sleep "$SLEEP_BETWEEN"
run_in_terminal "${PREFIX}${CMD3}"
