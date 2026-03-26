#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/docker-compose.yml"

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

if command -v xhost >/dev/null 2>&1; then
  xhost +local:root >/dev/null 2>&1 || true
fi

echo "[gui-run] DISPLAY=${DISPLAY}"
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
