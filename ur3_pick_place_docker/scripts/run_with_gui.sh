#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"
HOST_CONFIG_FILE="${HOST_CONFIG_FILE:-${ROOT_DIR}/host.env}"

read_host_config_var() {
  local key="$1"

  if [ ! -f "${HOST_CONFIG_FILE}" ]; then
    return 1
  fi

  awk -F= -v key="${key}" '
    /^[[:space:]]*#/ {next}
    /^[[:space:]]*$/ {next}
    {
      line=$0
      sub(/^[[:space:]]+/, "", line)
      split(line, kv, "=")
      cfg_key=kv[1]
      gsub(/[[:space:]]+$/, "", cfg_key)
      if (cfg_key == key) {
        val=substr(line, index(line, "=") + 1)
        sub(/^[[:space:]]+/, "", val)
        sub(/[[:space:]]+$/, "", val)
        gsub(/^"|"$/, "", val)
        gsub(/^'\''|'\''$/, "", val)
        print val
      }
    }
  ' "${HOST_CONFIG_FILE}" | tail -n 1
}

set_managed_var() {
  local key="$1"
  local default="$2"
  local value

  value="$(read_host_config_var "${key}" || true)"
  if [ -n "${value}" ]; then
    export "${key}=${value}"
    return
  fi

  export "${key}=${default}"
}

detect_display() {
  if [ -n "${DISPLAY:-}" ]; then
    printf '%s\n' "${DISPLAY}"
    return
  fi

  if [ -S /tmp/.X11-unix/X0 ]; then
    printf '%s\n' ":0"
    return
  fi

  local first_socket
  first_socket="$(ls /tmp/.X11-unix/X* 2>/dev/null | head -n 1 || true)"
  if [ -n "${first_socket}" ]; then
    printf ':%s\n' "$(basename "${first_socket}" | sed 's/^X//')"
    return
  fi

  printf '%s\n' ""
}

detect_xauthority_host() {
  if [ -n "${XAUTHORITY_HOST:-}" ] && [ -f "${XAUTHORITY_HOST}" ]; then
    printf '%s\n' "${XAUTHORITY_HOST}"
    return
  fi

  if [ -n "${XAUTHORITY:-}" ] && [ -f "${XAUTHORITY}" ]; then
    printf '%s\n' "${XAUTHORITY}"
    return
  fi

  if command -v xauth >/dev/null 2>&1; then
    local xauth_file
    xauth_file="$(xauth info 2>/dev/null | awk -F': *' '/Authority file/ {print $2}')"
    if [ -n "${xauth_file}" ] && [ -f "${xauth_file}" ]; then
      printf '%s\n' "${xauth_file}"
      return
    fi
  fi

  if [ -f "${HOME}/.Xauthority" ]; then
    printf '%s\n' "${HOME}/.Xauthority"
    return
  fi

  printf '%s\n' ""
}

DISPLAY_VALUE="$(detect_display)"
if [ -z "${DISPLAY_VALUE}" ]; then
  echo "[gui-run] ERROR: Unable to detect DISPLAY. Start from a desktop terminal and export DISPLAY (for example :0)." >&2
  exit 1
fi
export DISPLAY="${DISPLAY_VALUE}"

XAUTHORITY_HOST_VALUE="$(detect_xauthority_host)"
if [ -n "${XAUTHORITY_HOST_VALUE}" ]; then
  export XAUTHORITY_HOST="${XAUTHORITY_HOST_VALUE}"
fi

# Managed runtime config values come from host.env (when present) or defaults.
set_managed_var "UR_TYPE" "ur3"
set_managed_var "ROS_DOMAIN_ID" "0"
set_managed_var "LAUNCH_RVIZ" "0"
set_managed_var "REQUIRE_GUI" "1"
set_managed_var "RUN_PICK_PLACE_CLIENT" "1"
set_managed_var "USE_WS_OVERLAY" "0"
set_managed_var "SIM_BACKEND" "upstream"
set_managed_var "ARM_ACTION_NAME" "/scaled_joint_trajectory_controller/follow_joint_trajectory"
set_managed_var "IK_GROUP_NAME" "ur_manipulator"
set_managed_var "REQUIRE_GRIPPER" "1"
set_managed_var "WORLD_FILE" "/ws/src/UR3_ROS2_PICK_AND_PLACE/ur_gazebo/worlds/pick_and_place_demo.world"
set_managed_var "POSE_FRAME" "base_link"
set_managed_var "PICK_X" "0.35"
set_managed_var "PICK_Y" "0.15"
set_managed_var "PICK_Z" "0.12"
set_managed_var "PLACE_X" "0.35"
set_managed_var "PLACE_Y" "-0.20"
set_managed_var "PLACE_Z" "0.12"

if command -v xhost >/dev/null 2>&1; then
  xhost +local:root >/dev/null 2>&1 || true
fi

echo "[gui-run] DISPLAY=${DISPLAY}"
if [ -f "${HOST_CONFIG_FILE}" ]; then
  echo "[gui-run] HOST_CONFIG_FILE=${HOST_CONFIG_FILE}"
else
  echo "[gui-run] HOST_CONFIG_FILE not found, using launcher defaults"
fi
echo "[gui-run] LAUNCH_RVIZ=${LAUNCH_RVIZ}"
if [ -n "${XAUTHORITY_HOST:-}" ]; then
  echo "[gui-run] XAUTHORITY_HOST=${XAUTHORITY_HOST}"
else
  echo "[gui-run] WARNING: No XAUTHORITY host file detected; GUI auth may fail." >&2
fi

cd "${ROOT_DIR}"

if [ "$#" -eq 0 ]; then
  set -- up -d ur3_sim
fi

docker compose -f "${COMPOSE_FILE}" "$@"
