#!/usr/bin/env bash

set -e

USERNAME="${USERNAME:-developer}"
ROS_WS="${ROS_WS:-/workspaces/moxynova_ws}"
LOCAL_UID="${LOCAL_UID:-1000}"
LOCAL_GID="${LOCAL_GID:-1000}"

if [[ "$(id -g "${USERNAME}")" != "${LOCAL_GID}" ]]; then
    groupmod -o -g "${LOCAL_GID}" "${USERNAME}"
fi

if [[ "$(id -u "${USERNAME}")" != "${LOCAL_UID}" ]]; then
    usermod -o -u "${LOCAL_UID}" "${USERNAME}"
fi

mkdir -p \
    "${ROS_WS}/src" \
    "${ROS_WS}/build" \
    "${ROS_WS}/install" \
    "${ROS_WS}/log" \
    "/home/${USERNAME}/.ros" \
    "/tmp/runtime-${USERNAME}"

chown -R "${USERNAME}:${USERNAME}" \
    "${ROS_WS}/build" \
    "${ROS_WS}/install" \
    "${ROS_WS}/log" \
    "/home/${USERNAME}/.ros" \
    "/tmp/runtime-${USERNAME}"

chmod 700 "/tmp/runtime-${USERNAME}"

export HOME="/home/${USERNAME}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-${USERNAME}}"

if [[ $# -eq 0 ]]; then
    set -- bash
fi

exec gosu "${USERNAME}" bash -lc "source /opt/ros/${ROS_DISTRO}/setup.bash; if [ -f ${ROS_WS}/install/setup.bash ]; then source ${ROS_WS}/install/setup.bash; fi; exec \"\$@\"" bash "$@"
