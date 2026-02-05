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

CMD1='ros2 launch ur_gazebo ur.gazebo.launch.py'
CMD2='ros2 launch moveit_config move_group.launch.py'
CMD3='python3 /ws/src/UR3_ROS2_PICK_AND_PLACE/ur_system_tests/scripts/arm_gripper_loop_controller.py'

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
