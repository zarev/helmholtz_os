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

run_in_terminal "${PREFIX}${CMD1}"
sleep "$SLEEP_BETWEEN"
run_in_terminal "${PREFIX}${CMD2}"
sleep "$SLEEP_BETWEEN"
run_in_terminal "${PREFIX}${CMD3}"
