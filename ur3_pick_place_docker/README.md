# UR3 Pick and Place Docker Service

This service runs a UR3 Gazebo simulation, brings up MoveIt, and executes the
action client at `ws/pick_place_moveit_action.py`.

## What Changed

- The Docker image now installs these ROS Jazzy packages during build:
  - `ros-jazzy-ur`
  - `ros-jazzy-ur-moveit-config`
  - `ros-jazzy-ur-simulation-gz`
  - `ros-jazzy-moveit-msgs`
- Container startup now launches:
  1. `ros2 launch ur_gazebo ur.gazebo.launch.py ur_type:=ur3 use_sim_time:=true`
  2. `ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur3 use_sim_time:=true launch_rviz:=0`
  3. waits for `/arm_controller/follow_joint_trajectory`, `/compute_ik`, `/gripper_controller/gripper_cmd`
  3. runs `python3 /ws/pick_place_moveit_action.py`

## Prerequisites

- Docker and Docker Compose plugin installed.
- Linux host with X11 available if you want GUI windows from Gazebo/RViz.
- Access to Docker daemon (`sudo` may be required on this host).
- For GUI mode, allow local root X11 access on host:

```bash
xhost +local:root
```

## Build

From this directory:

```bash
docker compose build
```

If your user is not in the docker group:

```bash
sudo docker compose build
```

## Run

From this directory:

```bash
docker compose up
```

Recommended for GUI sessions (auto-detects DISPLAY and XAUTHORITY, applies xhost):

```bash
bash scripts/run_with_gui.sh
```

Host runtime values used by the helper are read from `host.env` in this folder.

Edit `host.env` for values such as:

- `LAUNCH_RVIZ` (default `0` for headless RViz)
- `RUN_PICK_PLACE_CLIENT`
- `WORLD_FILE`
- `SIM_BACKEND`
- `REQUIRE_GRIPPER`

This keeps launcher behavior deterministic and avoids accidental overrides from exported shell variables.

You can pass any compose args through the helper:

```bash
bash scripts/run_with_gui.sh down --remove-orphans
bash scripts/run_with_gui.sh up -d ur3_sim
```

With `sudo` if needed:

```bash
sudo docker compose up
```

From repository root (recommended for deployment scripts):

```bash
sudo docker compose -f ur3_pick_place_docker/docker-compose.yml up --build
```

The service default command is `/run_ur3_pick_place.sh`, which launches the
simulation stack and then starts the pick and place client.

The service includes a healthcheck that validates `/move_action` and `/clock`.

## Optional Configuration

When using `bash scripts/run_with_gui.sh`, set managed runtime values in `host.env`.
If you run `docker compose up` directly, inline environment variables still work.

- Set robot type (default is `ur3`):

```bash
UR_TYPE=ur3e docker compose up
```

- Set ROS domain id:

```bash
ROS_DOMAIN_ID=10 docker compose up
```

- Enable RViz GUI when running compose directly (helper uses `.host.env`):

```bash
LAUNCH_RVIZ=1 docker compose up
```

- Override the Gazebo world file (default auto-detects populated pick-place world):

```bash
WORLD_FILE=/opt/ros/jazzy/share/ur_gazebo/worlds/pick_and_place_demo.world docker compose up
```

Default selection order if `WORLD_FILE` is unset:

- `/ws/install/ur_gazebo/share/ur_gazebo/worlds/pick_and_place_demo.world`
- `/opt/ros/jazzy/share/ur_gazebo/worlds/pick_and_place_demo.world`
- fallback: `empty.sdf`

If a provided `WORLD_FILE` does not exist in the container, startup falls back to `empty.sdf`.

- Keep the simulator up without auto-running the action client:

```bash
RUN_PICK_PLACE_CLIENT=0 docker compose up
```

- Skip GUI preflight checks (headless/CI scenarios):

```bash
REQUIRE_GUI=0 docker compose up
```

## Logs and Verification

- Service logs:

```bash
docker compose logs -f ur3_sim
```

- Simulation and MoveIt launch logs inside container:

```bash
docker exec ur3_sim tail -f /tmp/ur_sim_control.log
docker exec ur3_sim tail -f /tmp/move_group.log
```

- Verify arm action exists:

```bash
docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list | grep /arm_controller/follow_joint_trajectory'
```

- Verify gripper action exists:

```bash
docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list | grep /gripper_controller/gripper_cmd'
```

- Verify `/compute_ik` exists:

```bash
docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 service list | grep /compute_ik'
```

- Verify Gazebo clock is active:

```bash
docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && timeout 5 ros2 topic echo /clock --once'
```

- Verify Gazebo (and optional RViz) processes:

```bash
docker exec ur3_sim bash -lc 'ps -ef | grep -E "gz sim|rviz2" | grep -v grep'
```

Expected startup output includes:

- `/arm_controller/follow_joint_trajectory is available`
- `/compute_ik is available`
- `/gripper_controller/gripper_cmd is available`

If startup fails, inspect `/tmp/ur_sim_control.log` and `/tmp/move_group.log` in the container.

Common issue:

- Qt/X11 display errors (`could not connect to display :0`)
  - Run `xhost +local:root` on the host
  - Ensure `DISPLAY` is exported on the host
  - Restart the service

## Stop

```bash
docker compose down
```