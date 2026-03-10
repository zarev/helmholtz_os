# helmholtz_os

Monorepo for robotics, scraping, and service components.

## UR3 Pick and Place (Docker)

The UR3 Docker service is configured to run simulation + MoveIt + action client automatically.

- Guide: [ur3_pick_place_docker/README.md](ur3_pick_place_docker/README.md)
- Service folder: [ur3_pick_place_docker](ur3_pick_place_docker)

Quick start:

```bash
cd ur3_pick_place_docker
sudo docker compose up -d --build
```

Verification:

```bash
sudo docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list | grep /move_action'
```

If `/move_action` is listed, the MoveIt action server is up and the pick-and-place client can connect.
