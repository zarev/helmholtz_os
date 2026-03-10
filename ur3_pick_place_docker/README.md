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
  1. `ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur3`
  2. waits for `/move_action`
  3. runs `python3 /ws/pick_place_moveit_action.py`

## Prerequisites

- Docker and Docker Compose plugin installed.
- Linux host with X11 available if you want GUI windows from Gazebo/RViz.
- Access to Docker daemon (`sudo` may be required on this host).

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

```bash
docker compose up
```

With `sudo` if needed:

```bash
sudo docker compose up
```

The service default command is `/run_ur3_pick_place.sh`, which launches the
simulation stack and then starts the pick and place client.

## Optional Configuration

- Set robot type (default is `ur3`):

```bash
UR_TYPE=ur3e docker compose up
```

- Set ROS domain id:

```bash
ROS_DOMAIN_ID=10 docker compose up
```

## Logs and Verification

- Service logs:

```bash
docker compose logs -f ur3_sim
```

- MoveIt/simulation launch log inside container:

```bash
docker exec ur3_sim tail -f /tmp/ur_sim_moveit.log
```

- Verify `/move_action` exists:

```bash
docker exec ur3_sim bash -lc 'source /opt/ros/jazzy/setup.bash && ros2 action list | grep /move_action'
```

Expected client output includes:

- `Waiting for MoveIt action server...`
- `Connected to MoveIt`

## Stop

```bash
docker compose down
```