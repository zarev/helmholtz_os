# ROS 2 workspace

This repository ships a small ROS 2 workspace (`ros2_ws`) with a minimal simulation loop to validate the container toolchain.

## Quickstart (Docker Compose)

1. Start the ROS 2 container:
   ```bash
   docker compose up -d ros2
   ```

2. Build the workspace inside the container:
   ```bash
   docker exec ros2 bash -c "source /opt/ros/humble/setup.bash && cd /root/ros2_ws && colcon build"
   ```

3. Run the simulation:
   ```bash
   docker exec -it ros2 bash -c "source /opt/ros/humble/setup.bash && source /root/ros2_ws/install/setup.bash && ros2 launch minimal_sim sim_launch.py"
   ```

4. Inspect messages (from another terminal):
   ```bash
   docker exec -it ros2 bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /sim/pose"
   ```

## Quickstart (Dev Container)
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
