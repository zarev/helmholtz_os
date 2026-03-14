#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${CONTAINER:-ur3_sim}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT_DIR="${OUT_DIR:-${REPO_DIR}/screenshots}"
COUNT="1"
INTERVAL="2"

usage() {
  cat <<'USAGE'
Usage: capture_sim_screenshots.sh [--count N] [--interval SEC] [--out-dir PATH] [--container NAME]

Examples:
  ./scripts/capture_sim_screenshots.sh
  ./scripts/capture_sim_screenshots.sh --count 5 --interval 1.5
  CONTAINER=ur3_sim ./scripts/capture_sim_screenshots.sh --out-dir ./screenshots
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --count)
      COUNT="$2"
      shift 2
      ;;
    --interval)
      INTERVAL="$2"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    --container)
      CONTAINER="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -lt 1 ]]; then
  echo "--count must be a positive integer" >&2
  exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "--interval must be a non-negative number" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

DOCKER_USE_SG=0
if ! docker ps >/dev/null 2>&1; then
  if command -v sg >/dev/null 2>&1 && sg docker -c "docker ps >/dev/null 2>&1"; then
    DOCKER_USE_SG=1
  else
    echo "Docker is not accessible for the current user. Add user to docker group or run with proper permissions." >&2
    exit 1
  fi
fi

run_docker() {
  if [[ "$DOCKER_USE_SG" -eq 0 ]]; then
    docker "$@"
  else
    local cmd="docker"
    local arg
    for arg in "$@"; do
      cmd+=" $(printf '%q' "$arg")"
    done
    sg docker -c "$cmd"
  fi
}

capture_in_container() {
  run_docker exec "$CONTAINER" bash -lc 'set -euo pipefail; export LD_LIBRARY_PATH=/opt/ros/jazzy/opt/gz_cmake_vendor/lib:/opt/ros/jazzy/opt/gz_common_vendor/lib:/opt/ros/jazzy/opt/gz_dartsim_vendor/lib:/opt/ros/jazzy/opt/gz_fuel_tools_vendor/lib:/opt/ros/jazzy/opt/gz_gui_vendor/lib:/opt/ros/jazzy/opt/gz_math_vendor/lib:/opt/ros/jazzy/opt/gz_msgs_vendor/lib:/opt/ros/jazzy/opt/gz_ogre_next_vendor/lib:/opt/ros/jazzy/opt/gz_physics_vendor/lib:/opt/ros/jazzy/opt/gz_plugin_vendor/lib:/opt/ros/jazzy/opt/gz_rendering_vendor/lib:/opt/ros/jazzy/opt/gz_sensors_vendor/lib:/opt/ros/jazzy/opt/gz_sim_vendor/lib:/opt/ros/jazzy/opt/gz_tools_vendor/lib:/opt/ros/jazzy/opt/gz_transport_vendor/lib:/opt/ros/jazzy/opt/gz_utils_vendor/lib:/opt/ros/jazzy/opt/rviz_ogre_vendor/lib:/opt/ros/jazzy/opt/sdformat_vendor/lib; export GZ_CONFIG_PATH=/opt/ros/jazzy/opt/gz_cmake_vendor/share/gz:/opt/ros/jazzy/opt/gz_common_vendor/share/gz:/opt/ros/jazzy/opt/gz_fuel_tools_vendor/share/gz:/opt/ros/jazzy/opt/gz_gui_vendor/share/gz:/opt/ros/jazzy/opt/gz_msgs_vendor/share/gz:/opt/ros/jazzy/opt/gz_plugin_vendor/share/gz:/opt/ros/jazzy/opt/gz_rendering_vendor/share/gz:/opt/ros/jazzy/opt/gz_sim_vendor/share/gz:/opt/ros/jazzy/opt/gz_tools_vendor/share/gz:/opt/ros/jazzy/opt/gz_transport_vendor/share/gz:/opt/ros/jazzy/opt/sdformat_vendor/share/gz; /opt/ros/jazzy/opt/gz_tools_vendor/bin/gz service -s /gui/screenshot --reqtype gz.msgs.StringMsg --reptype gz.msgs.Boolean --timeout 5000 --req "data: \"\"" >/dev/null; sleep 1; latest=$(ls -1t /root/.gz/gui/pictures/*.png 2>/dev/null | head -n1 || true); if [[ -n "$latest" ]]; then echo "$latest"; fi'
}

echo "Capturing ${COUNT} screenshot(s) from ${CONTAINER} into ${OUT_DIR}"
for ((i=1; i<=COUNT; i++)); do
  latest_path="$(capture_in_container | tail -n1)"
  if [[ -z "$latest_path" ]]; then
    echo "Failed to find screenshot in container after trigger" >&2
    exit 1
  fi

  stamp="$(date +%Y%m%d_%H%M%S)"
  out_file="${OUT_DIR}/sim_${stamp}_$(printf '%02d' "$i").png"
  run_docker cp "${CONTAINER}:${latest_path}" "$out_file" >/dev/null
  echo "$out_file"

  if [[ "$i" -lt "$COUNT" ]]; then
    sleep "$INTERVAL"
  fi
done
