#!/usr/bin/env bash

set -euo pipefail

ROS_WS="${ROS_WS:-/workspaces/moxynova_ws}"
DESCRIPTION_FILE="${UR_DESCRIPTION_FILE:-${ROS_WS}/src/lab_robot_description/urdf/ur_with_robotiq_2f_85.urdf.xacro}"
WORLD_FILE="${PICK_PLACE_WORLD_FILE:-${ROS_WS}/src/lab_robot_gazebo/worlds/pick_and_place_demo.world}"
CONTROLLERS_FILE="${UR_CONTROLLERS_FILE:-${ROS_WS}/src/lab_robot_control/config/ur_with_gripper_controllers.yaml}"
UR_TYPE="${UR_TYPE:-ur3e}"
ARM_ACTION="${ARM_TRAJECTORY_ACTION:-/scaled_joint_trajectory_controller/follow_joint_trajectory}"
GRIPPER_ACTION="${GRIPPER_TRAJECTORY_ACTION:-/gripper_controller/follow_joint_trajectory}"
STARTUP_TIMEOUT_SEC="${STARTUP_TIMEOUT_SEC:-120}"
LAUNCH_RVIZ="${LAUNCH_RVIZ:-false}"
GAZEBO_GUI="${GAZEBO_GUI:-true}"
ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

if [[ ! -f "${DESCRIPTION_FILE}" ]]; then
    echo "Description file not found: ${DESCRIPTION_FILE}" >&2
    exit 1
fi

if [[ ! -f "${WORLD_FILE}" ]]; then
    echo "World file not found: ${WORLD_FILE}" >&2
    exit 1
fi

if [[ ! -f "${CONTROLLERS_FILE}" ]]; then
    echo "Controllers file not found: ${CONTROLLERS_FILE}" >&2
    exit 1
fi

export GZ_SIM_RESOURCE_PATH="${ROS_WS}/src/lab_robot_gazebo/models:${ROS_WS}/install/robotiq_2f_85_gripper_visualization/share:/opt/ros/${ROS_DISTRO}/share${GZ_SIM_RESOURCE_PATH:+:${GZ_SIM_RESOURCE_PATH}}"
export ROS_DOMAIN_ID

wait_for_ros_resource() {
    local kind="$1"
    local name="$2"
    local timeout="$3"
    local start

    start=$(date +%s)
    while true; do
        case "${kind}" in
            service)
                if ros2 service list 2>/dev/null | grep -Fxq "${name}"; then
                    return 0
                fi
                ;;
            action)
                if ros2 action list 2>/dev/null | grep -Fxq "${name}"; then
                    return 0
                fi
                ;;
            topic)
                if ros2 topic list 2>/dev/null | grep -Fxq "${name}"; then
                    return 0
                fi
                ;;
            *)
                echo "Unsupported wait type: ${kind}" >&2
                return 1
                ;;
        esac

        if (( $(date +%s) - start >= timeout )); then
            echo "Timed out waiting for ${kind}: ${name}" >&2
            return 1
        fi

        sleep 2
    done
}

wait_for_controller_state() {
    local controller_name="$1"
    local desired_state="$2"
    local timeout="$3"
    local start
    local output

    start=$(date +%s)
    while true; do
        output=$(ros2 service call /controller_manager/list_controllers \
            controller_manager_msgs/srv/ListControllers "{}" 2>/dev/null || true)

        if grep -Fq "name='${controller_name}', state='${desired_state}'" <<<"${output}"; then
            return 0
        fi

        if (( $(date +%s) - start >= timeout )); then
            echo "Timed out waiting for controller ${controller_name} to reach state ${desired_state}" >&2
            return 1
        fi

        sleep 2
    done
}

cleanup() {
    if [[ -n "${moveit_pid:-}" ]]; then
        kill "${moveit_pid}" 2>/dev/null || true
        wait "${moveit_pid}" 2>/dev/null || true
    fi
    if [[ -n "${gazebo_pid:-}" ]]; then
        kill "${gazebo_pid}" 2>/dev/null || true
        wait "${gazebo_pid}" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

echo "Launching UR Gazebo + controllers with:"
echo "  description: ${DESCRIPTION_FILE}"
echo "  world:       ${WORLD_FILE}"
echo "  controllers: ${CONTROLLERS_FILE}"
ros2 launch lab_robot_control ur_with_gripper_sim.launch.py \
    "ur_type:=${UR_TYPE}" \
    "description_file:=${DESCRIPTION_FILE}" \
    "world_file:=${WORLD_FILE}" \
    "controllers_file:=${CONTROLLERS_FILE}" \
    "gazebo_gui:=${GAZEBO_GUI}" \
    launch_rviz:=false \
    &
gazebo_pid=$!

wait_for_ros_resource topic /robot_description "${STARTUP_TIMEOUT_SEC}"
wait_for_controller_state scaled_joint_trajectory_controller active "${STARTUP_TIMEOUT_SEC}"
wait_for_controller_state gripper_controller active "${STARTUP_TIMEOUT_SEC}"

echo "Waiting for a non-empty joint state before launching MoveIt"
ros2 run lab_utils wait_for_nonempty_joint_state --ros-args \
    -p use_sim_time:=true \
    -p timeout_sec:="${STARTUP_TIMEOUT_SEC}"

echo "Launching MoveIt (RViz: ${LAUNCH_RVIZ})"
ros2 launch ur_moveit_config ur_moveit.launch.py \
    "ur_type:=${UR_TYPE}" \
    use_sim_time:=true \
    "launch_rviz:=${LAUNCH_RVIZ}" &
moveit_pid=$!

wait_for_ros_resource service /compute_ik "${STARTUP_TIMEOUT_SEC}"

echo "Starting pick-and-place demo node"
ros2 run lab_demo_tasks pick_place_moveit_action

echo "Demo node exited. Gazebo and MoveIt remain active until the container is stopped."
wait "${moveit_pid}"
