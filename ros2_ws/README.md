# ROS 2 workspace

This repository ships a small ROS 2 workspace (`ros2_ws`) with a minimal simulation loop to validate the container toolchain.

## Quickstart
1. Open the repo in the provided dev container (`.devcontainer`).
2. Build the workspace once inside the container:
   ```bash
   cd /workspaces/helmholtz_os/ros2_ws
   colcon build --symlink-install
   ```
3. Source the overlay and run the sim loop:
   ```bash
   source install/setup.bash
   ros2 run minimal_sim sim_loop
   ```
4. Inspect messages from another terminal in the container:
   ```bash
   source install/setup.bash
   ros2 topic echo /sim/pose
   ros2 topic echo /sim/status
   ```

The node publishes a circular `Pose2D` trajectory at 10 Hz on `sim/pose` and a heartbeat string once per second on `sim/status`.
