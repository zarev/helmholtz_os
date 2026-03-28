#!/usr/bin/env bash
set -euo pipefail

CONTAINER="${CONTAINER:-ur3_sim}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
OUT_DIR="${OUT_DIR:-${REPO_DIR}/screenshots}"

# Expected side-profile view: cylinder on left, arm on right.
EXPECT_X="${EXPECT_X:-2.45}"
EXPECT_Y="${EXPECT_Y:--1.35}"
EXPECT_Z="${EXPECT_Z:-1.25}"
EXPECT_QX="${EXPECT_QX:--0.12}"
EXPECT_QY="${EXPECT_QY:-0.33}"
EXPECT_QZ="${EXPECT_QZ:-0.89}"
EXPECT_QW="${EXPECT_QW:-0.28}"

POS_TOL="${POS_TOL:-0.15}"
ROT_TOL="${ROT_TOL:-0.12}"
CAPTURE_SCREENSHOT="${CAPTURE_SCREENSHOT:-1}"

usage() {
  cat <<'USAGE'
Usage: validate_gazebo_camera_view.sh [--container NAME] [--out-dir PATH]

Environment overrides:
  EXPECT_X, EXPECT_Y, EXPECT_Z
  EXPECT_QX, EXPECT_QY, EXPECT_QZ, EXPECT_QW
  POS_TOL, ROT_TOL
  CAPTURE_SCREENSHOT=0|1

Exit codes:
  0 if the live Gazebo GUI camera pose matches the expected pose within tolerance
  1 if the pose does not match or the running sim cannot be queried
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --container)
      CONTAINER="$2"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! docker ps --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  echo "Container $CONTAINER is not running." >&2
  exit 1
fi

POSE_RAW="$(docker exec "$CONTAINER" bash -lc '
  set -euo pipefail
  export LD_LIBRARY_PATH=/opt/ros/jazzy/opt/gz_cmake_vendor/lib:/opt/ros/jazzy/opt/gz_common_vendor/lib:/opt/ros/jazzy/opt/gz_dartsim_vendor/lib:/opt/ros/jazzy/opt/gz_fuel_tools_vendor/lib:/opt/ros/jazzy/opt/gz_gui_vendor/lib:/opt/ros/jazzy/opt/gz_math_vendor/lib:/opt/ros/jazzy/opt/gz_msgs_vendor/lib:/opt/ros/jazzy/opt/gz_ogre_next_vendor/lib:/opt/ros/jazzy/opt/gz_physics_vendor/lib:/opt/ros/jazzy/opt/gz_plugin_vendor/lib:/opt/ros/jazzy/opt/gz_rendering_vendor/lib:/opt/ros/jazzy/opt/gz_sensors_vendor/lib:/opt/ros/jazzy/opt/gz_sim_vendor/lib:/opt/ros/jazzy/opt/gz_tools_vendor/lib:/opt/ros/jazzy/opt/gz_transport_vendor/lib:/opt/ros/jazzy/opt/gz_utils_vendor/lib:/opt/ros/jazzy/opt/rviz_ogre_vendor/lib:/opt/ros/jazzy/opt/sdformat_vendor/lib
  export GZ_CONFIG_PATH=/opt/ros/jazzy/opt/gz_cmake_vendor/share/gz:/opt/ros/jazzy/opt/gz_common_vendor/share/gz:/opt/ros/jazzy/opt/gz_fuel_tools_vendor/share/gz:/opt/ros/jazzy/opt/gz_gui_vendor/share/gz:/opt/ros/jazzy/opt/gz_msgs_vendor/share/gz:/opt/ros/jazzy/opt/gz_plugin_vendor/share/gz:/opt/ros/jazzy/opt/gz_rendering_vendor/share/gz:/opt/ros/jazzy/opt/gz_sim_vendor/share/gz:/opt/ros/jazzy/opt/gz_tools_vendor/share/gz:/opt/ros/jazzy/opt/gz_transport_vendor/share/gz:/opt/ros/jazzy/opt/sdformat_vendor/share/gz
  /opt/ros/jazzy/opt/gz_tools_vendor/bin/gz topic -e -n 1 -t /gui/camera/pose
')"

if [[ -z "$POSE_RAW" ]]; then
  echo "Failed to read /gui/camera/pose from $CONTAINER." >&2
  exit 1
fi

ACTUAL_VALUES="$(printf '%s\n' "$POSE_RAW" | awk '
  /position *{/ {section="position"; next}
  /orientation *{/ {section="orientation"; next}
  /^}/ {section=""; next}
  section == "position" && $1 == "x:" {px=$2}
  section == "position" && $1 == "y:" {py=$2}
  section == "position" && $1 == "z:" {pz=$2}
  section == "orientation" && $1 == "x:" {qx=$2}
  section == "orientation" && $1 == "y:" {qy=$2}
  section == "orientation" && $1 == "z:" {qz=$2}
  section == "orientation" && $1 == "w:" {qw=$2}
  END {
    if (px == "") px = 0
    if (py == "") py = 0
    if (pz == "") pz = 0
    if (qx == "") qx = 0
    if (qy == "") qy = 0
    if (qz == "") qz = 0
    if (qw == "") qw = 0
    printf "%s %s %s %s %s %s %s\n", px, py, pz, qx, qy, qz, qw
  }
')"

read -r ACTUAL_X ACTUAL_Y ACTUAL_Z ACTUAL_QX ACTUAL_QY ACTUAL_QZ ACTUAL_QW <<< "$ACTUAL_VALUES"

VALIDATION_RESULT="$(awk \
  -v ax="$ACTUAL_X" -v ay="$ACTUAL_Y" -v az="$ACTUAL_Z" \
  -v aqx="$ACTUAL_QX" -v aqy="$ACTUAL_QY" -v aqz="$ACTUAL_QZ" -v aqw="$ACTUAL_QW" \
  -v ex="$EXPECT_X" -v ey="$EXPECT_Y" -v ez="$EXPECT_Z" \
  -v eqx="$EXPECT_QX" -v eqy="$EXPECT_QY" -v eqz="$EXPECT_QZ" -v eqw="$EXPECT_QW" \
  -v pt="$POS_TOL" -v rt="$ROT_TOL" 'BEGIN {
    ok = 1
    if ((ax - ex > pt) || (ex - ax > pt)) ok = 0
    if ((ay - ey > pt) || (ey - ay > pt)) ok = 0
    if ((az - ez > pt) || (ez - az > pt)) ok = 0
    if ((aqx - eqx > rt) || (eqx - aqx > rt)) ok = 0
    if ((aqy - eqy > rt) || (eqy - aqy > rt)) ok = 0
    if ((aqz - eqz > rt) || (eqz - aqz > rt)) ok = 0
    if ((aqw - eqw > rt) || (eqw - aqw > rt)) ok = 0
    print ok ? "PASS" : "FAIL"
  }')"

echo "Expected camera pose:"
echo "  position=($EXPECT_X, $EXPECT_Y, $EXPECT_Z)"
echo "  orientation=($EXPECT_QX, $EXPECT_QY, $EXPECT_QZ, $EXPECT_QW)"
echo "Actual camera pose:"
echo "  position=($ACTUAL_X, $ACTUAL_Y, $ACTUAL_Z)"
echo "  orientation=($ACTUAL_QX, $ACTUAL_QY, $ACTUAL_QZ, $ACTUAL_QW)"
echo "Validation result: $VALIDATION_RESULT"

if [[ "$CAPTURE_SCREENSHOT" == "1" ]]; then
  SCREENSHOT_PATH="$(${SCRIPT_DIR}/capture_sim_screenshots.sh --count 1 --out-dir "$OUT_DIR" --container "$CONTAINER" | tail -n 1)"
  echo "Screenshot: $SCREENSHOT_PATH"
fi

if [[ "$VALIDATION_RESULT" != "PASS" ]]; then
  exit 1
fi