#!/usr/bin/env bash
set -e

cd /ws

rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy

colcon build --symlink-install
