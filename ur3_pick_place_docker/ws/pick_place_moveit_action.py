#!/usr/bin/env python3

import math
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import rclpy
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from geometry_msgs.msg import PoseStamped
from moveit_msgs.msg import RobotState
from moveit_msgs.srv import GetPositionIK
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from trajectory_msgs.msg import JointTrajectoryPoint


DEFAULT_BATTERY_MODEL_NAME = "red_cylinder"
DEFAULT_LOOP_MODE = "move_to_battery"
UR_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
SAFE_HOME_JOINTS = [-0.1, -1.6315, 0.0, 1.8251, 0.0, 1.2844]
SAFE_MOVE_RPY_CANDIDATES = [
    (math.pi, 0.0, math.pi / 2.0),
    (math.pi, 0.0, -math.pi / 2.0),
    (math.pi, 0.0, 0.0),
    (0.0, 0.0, 0.0),
    (0.0, math.pi / 2.0, 0.0),
    (0.0, -math.pi / 2.0, 0.0),
]
LOOP_MODES = {
    "move_to_battery": "run_move_to_battery_loop",
    "battery_hover": "run_move_to_battery_loop",
}


class BatteryMoveClient(Node):
    def __init__(self, loop_name=None):
        super().__init__("ur3_battery_move")
        self.group_name = os.getenv("IK_GROUP_NAME", "ur_manipulator")
        self.arm_action_name = os.getenv(
            "ARM_ACTION_NAME",
            "/scaled_joint_trajectory_controller/follow_joint_trajectory",
        )
        self.arm = ActionClient(self, FollowJointTrajectory, self.arm_action_name)
        self.ik = self.create_client(GetPositionIK, "/compute_ik")
        self.last_joint_state = None
        self.last_orientation = None

        self.create_subscription(JointState, "/joint_states", self._joint_state_cb, 10)

        self.get_logger().info("Waiting for arm action and IK service...")
        if not self.arm.wait_for_server(timeout_sec=30.0):
            raise RuntimeError(f"Arm action server {self.arm_action_name} is unavailable")
        if not self.ik.wait_for_service(timeout_sec=30.0):
            raise RuntimeError("IK service /compute_ik is unavailable")

        wait_deadline = time.time() + 45.0
        while self.last_joint_state is None and time.time() < wait_deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
        if self.last_joint_state is None:
            raise RuntimeError("No /joint_states data received")

        self.get_logger().info(f"Arm action and IK service ready (arm action: {self.arm_action_name})")
        selected_loop = loop_name or os.getenv("ROBOT_LOOP_MODE", DEFAULT_LOOP_MODE)
        self.run_selected_loop(selected_loop)

    def _joint_state_cb(self, msg: JointState):
        self.last_joint_state = msg

    @staticmethod
    def _env_float(name, default):
        return float(os.getenv(name, str(default)))

    def _rpy_to_quat_tuple(self, roll, pitch, yaw):
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        return (
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy,
        )

    def _apply_quat(self, pose, quat):
        pose.pose.orientation.x = quat[0]
        pose.pose.orientation.y = quat[1]
        pose.pose.orientation.z = quat[2]
        pose.pose.orientation.w = quat[3]

    @staticmethod
    def _pose_at(x, y, z):
        pose = PoseStamped()
        pose.header.frame_id = os.getenv("POSE_FRAME", "base_link")
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0
        return pose

    @staticmethod
    def _parse_pose_text(pose_text):
        values = [float(value) for value in pose_text.split()]
        while len(values) < 6:
            values.append(0.0)
        return tuple(values[:6])

    def _arm_reached(self, target_positions):
        if self.last_joint_state is None:
            return False

        try:
            current_positions = [
                self.last_joint_state.position[self.last_joint_state.name.index(joint_name)]
                for joint_name in UR_JOINTS
            ]
        except ValueError:
            return False

        tolerance = self._env_float("ARM_REACHED_TOLERANCE", 0.12)
        return all(
            abs(current - target) <= tolerance
            for current, target in zip(current_positions, target_positions)
        )

    def _current_arm_joints(self):
        if self.last_joint_state is None:
            return list(SAFE_HOME_JOINTS)

        try:
            return [
                self.last_joint_state.position[self.last_joint_state.name.index(joint_name)]
                for joint_name in UR_JOINTS
            ]
        except ValueError:
            return list(SAFE_HOME_JOINTS)

    def compute_ik(self, pose, orientation_rpy_candidates=None):
        req = GetPositionIK.Request()
        req.ik_request.group_name = self.group_name
        req.ik_request.ik_link_name = os.getenv("MOVE_TARGET_LINK", "tool0")
        req.ik_request.pose_stamped = pose
        req.ik_request.timeout.sec = 4

        if self.last_joint_state is not None:
            state = RobotState()
            state.joint_state = self.last_joint_state
            req.ik_request.robot_state = state

        orientation_candidates = []
        if self.last_orientation is not None:
            orientation_candidates.append(self.last_orientation)
        for rpy in orientation_rpy_candidates or SAFE_MOVE_RPY_CANDIDATES:
            quat = self._rpy_to_quat_tuple(*rpy)
            if quat not in orientation_candidates:
                orientation_candidates.append(quat)

        response = None
        solutions = []
        reference_joints = self._current_arm_joints()
        for avoid_collisions in (True, False):
            req.ik_request.avoid_collisions = avoid_collisions
            for quat in orientation_candidates:
                self._apply_quat(pose, quat)
                req.ik_request.pose_stamped = pose
                future = self.ik.call_async(req)
                rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
                if not future.done():
                    self.get_logger().warn("IK request timed out; trying next orientation")
                    continue

                response = future.result()
                if response and response.error_code.val == response.error_code.SUCCESS:
                    candidate_joints = [
                        response.solution.joint_state.position[
                            response.solution.joint_state.name.index(joint_name)
                        ]
                        for joint_name in UR_JOINTS
                    ]
                    score = sum(
                        abs(candidate - reference)
                        for candidate, reference in zip(candidate_joints, reference_joints)
                    )
                    solutions.append((score, quat, candidate_joints))

        if solutions:
            _, best_quat, best_joints = min(solutions, key=lambda item: item[0])
            self.last_orientation = best_quat
            return best_joints

        if response is not None:
            self.get_logger().error(f"IK failed, error_code={response.error_code.val}")
        else:
            self.get_logger().error("IK failed, no response")
        return None

    def move_joints(self, joints, label, duration_seconds):
        goal = FollowJointTrajectory.Goal()
        point = JointTrajectoryPoint()
        point.positions = joints
        seconds = int(duration_seconds)
        nanoseconds = int((duration_seconds - seconds) * 1e9)
        point.time_from_start = Duration(sec=seconds, nanosec=nanoseconds)
        goal.trajectory.joint_names = UR_JOINTS
        goal.trajectory.points = [point]

        self.get_logger().info(label)
        goal_future = self.arm.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, goal_future, timeout_sec=20.0)
        goal_handle = goal_future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error(f"{label} goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        deadline = time.time() + self._env_float("ARM_MOTION_COMPLETE_SECONDS", 120.0)
        while time.time() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self._arm_reached(joints):
                self.get_logger().info(f"{label} reached target via joint-state check")
                return True
            if result_future.done() and result_future.result() is None:
                self.get_logger().error(f"{label} result not received")
                return False

        self.get_logger().error(f"{label} did not reach target before timeout")
        return False

    def move_pose(self, pose, label, duration_seconds):
        joints = self.compute_ik(pose, orientation_rpy_candidates=SAFE_MOVE_RPY_CANDIDATES)
        if joints is None:
            self.get_logger().error(f"{label} could not find an IK solution")
            return False
        return self.move_joints(joints, label, duration_seconds)

    def _resolve_world_model_pose(self, model_name, world_file):
        if not world_file:
            return None

        world_path = Path(world_file)
        if not world_path.is_file():
            self.get_logger().warn(
                f"WORLD_FILE {world_file} is unavailable; falling back to PICK_* coordinates"
            )
            return None

        try:
            world_tree = ET.parse(world_path)
        except (ET.ParseError, OSError) as exc:
            self.get_logger().warn(
                f"Failed to parse WORLD_FILE {world_file}: {exc}; falling back to PICK_* coordinates"
            )
            return None

        root = world_tree.getroot()
        for include in root.findall(".//include"):
            include_name = (include.findtext("name") or "").strip()
            include_uri = (include.findtext("uri") or "").strip()
            uri_model_name = include_uri.rsplit("/", 1)[-1] if include_uri else ""
            if include_name != model_name and uri_model_name != model_name:
                continue

            pose_text = (include.findtext("pose") or "0 0 0 0 0 0").strip()
            return self._parse_pose_text(pose_text)

        self.get_logger().warn(
            f"Model {model_name} was not found in WORLD_FILE {world_file}; falling back to PICK_* coordinates"
        )
        return None

    def resolve_battery_target(self):
        fallback_target = (
            self._env_float("PICK_X", 0.35),
            self._env_float("PICK_Y", 0.15),
            self._env_float("PICK_Z", 0.12),
        )

        world_file = os.getenv("WORLD_FILE", "")
        model_name = os.getenv("PICK_MODEL_NAME", DEFAULT_BATTERY_MODEL_NAME)
        world_pose = self._resolve_world_model_pose(model_name, world_file)
        if world_pose is None:
            self.get_logger().info(
                "Using fallback battery target x=%.3f y=%.3f z=%.3f" % fallback_target
            )
            return fallback_target

        battery_target = world_pose[:3]
        self.get_logger().info(
            "Resolved %s target from %s at x=%.3f y=%.3f z=%.3f"
            % (model_name, world_file, battery_target[0], battery_target[1], battery_target[2])
        )
        return battery_target

    def run_selected_loop(self, loop_name):
        loop_method_name = LOOP_MODES.get(loop_name)
        if loop_method_name is None:
            available = ", ".join(sorted(LOOP_MODES))
            raise RuntimeError(
                f"Unknown ROBOT_LOOP_MODE '{loop_name}'. Available modes: {available}"
            )

        self.get_logger().info(f"Starting loop mode: {loop_name}")
        getattr(self, loop_method_name)()

    def move_arm_to_battery(self):
        battery_x, battery_y, battery_z = self.resolve_battery_target()
        target_z = max(
            battery_z + self._env_float("BATTERY_TARGET_Z_OFFSET", 0.32),
            self._env_float("BATTERY_MIN_TARGET_Z", 0.45),
        )

        battery_target_pose = self._pose_at(battery_x, battery_y, target_z)

        if not self.move_joints(
            SAFE_HOME_JOINTS,
            "Move to safe raised joint pose",
            self._env_float("BATTERY_SAFE_HOME_SECONDS", 6.0),
        ):
            return False
        if not self.move_pose(
            battery_target_pose,
            "Move over the battery",
            self._env_float("BATTERY_TARGET_SECONDS", 8.0),
        ):
            return False

        self.get_logger().info(
            "Battery hover target reached at x=%.3f y=%.3f z=%.3f"
            % (battery_x, battery_y, target_z)
        )
        return True

    def run_move_to_battery_loop(self):
        if not self.move_arm_to_battery():
            return

        self.get_logger().info("Holding current pose above battery")
        while rclpy.ok() and os.getenv("HOLD_POSITION_AFTER_MOVE", "1") == "1":
            rclpy.spin_once(self, timeout_sec=0.5)


def main():
    rclpy.init()
    node = BatteryMoveClient(loop_name=os.getenv("ROBOT_LOOP_MODE", DEFAULT_LOOP_MODE))
    try:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
