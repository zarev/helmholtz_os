# helmholtz_os

Monorepo for robotics, scraping, and service components.

## UR3 Pick and Place (Docker)

The UR3 Docker service is configured to run simulation + MoveIt + action client automatically.

- Guide: [ur3_pick_place_docker/README.md](ur3_pick_place_docker/README.md)
- Service folder: [ur3_pick_place_docker](ur3_pick_place_docker)

Quick start:

```bash
xhost +local:root
sudo docker compose -f ur3_pick_place_docker/docker-compose.yml up --build
```

Verification:

```bash
sudo docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list | grep /arm_controller/follow_joint_trajectory'
sudo docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list | grep /gripper_controller/gripper_cmd'
sudo docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 service list | grep /compute_ik'
sudo docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && timeout 5 ros2 topic echo /clock --once'
```

If arm and gripper actions are listed, `/compute_ik` exists, and `/clock` returns a message, MoveIt and Gazebo are running.

By default, RViz GUI is disabled (`LAUNCH_RVIZ=0`) while MoveIt planning remains active.

For full deployment details (GUI prerequisites, healthchecks, optional headless mode), see the UR3 guide.
