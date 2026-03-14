#!/usr/bin/env python3

import time

import rclpy
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectoryPoint


class PickPlaceTrajectoryClient(Node):
    def __init__(self):
        super().__init__('pick_place_trajectory_client')

        self.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint',
        ]

        # Trajectory points chosen to create clear left-right motion around the scene.
        self.home_joints = [0.0, -1.20, 1.40, -1.80, -1.57, 0.0]
        self.pick_joints = [0.45, -1.35, 1.60, -1.85, -1.57, 0.45]
        self.place_joints = [-0.45, -1.35, 1.60, -1.85, -1.57, -0.45]

        self.arm_action = self._connect_arm_action()

    def _connect_arm_action(self):
        endpoints = [
            '/scaled_joint_trajectory_controller/follow_joint_trajectory',
            '/joint_trajectory_controller/follow_joint_trajectory',
        ]

        for endpoint in endpoints:
            client = ActionClient(self, FollowJointTrajectory, endpoint)
            self.get_logger().info(f'Waiting for arm action server: {endpoint}')
            if client.wait_for_server(timeout_sec=10.0):
                self.get_logger().info(f'Connected to arm action server: {endpoint}')
                return client

        self.get_logger().error('No arm trajectory action server became available')
        return None

    def send_arm_goal(self, positions, label: str, duration_sec: int = 3) -> bool:
        if self.arm_action is None:
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = [float(v) for v in positions]
        point.time_from_start = Duration(sec=duration_sec)
        goal.trajectory.points = [point]

        self.get_logger().info(f'Sending arm trajectory goal: {label}')
        send_future = self.arm_action.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=10.0)
        if not send_future.done() or send_future.result() is None:
            self.get_logger().error(f'Goal send timed out: {label}')
            return False

        goal_handle = send_future.result()
        if not goal_handle.accepted:
            self.get_logger().error(f'Goal rejected: {label}')
            return False

        # Some controllers execute correctly but delay/omit action result feedback.
        # Use a conservative dwell based on trajectory duration to avoid preempting.
        dwell_sec = float(duration_sec) + 1.0
        time.sleep(dwell_sec)
        self.get_logger().info(f'Goal dispatched: {label} (waited {dwell_sec:.1f}s)')
        return True

    def run_loop(self):
        if self.arm_action is None:
            return

        # Allow controllers to fully settle before commanding first motion.
        time.sleep(2.0)

        while rclpy.ok():
            ok = self.send_arm_goal(self.home_joints, 'home', duration_sec=3)
            ok = self.send_arm_goal(self.pick_joints, 'pick_approach', duration_sec=3) and ok
            ok = self.send_arm_goal(self.place_joints, 'place_approach', duration_sec=3) and ok
            ok = self.send_arm_goal(self.home_joints, 'home_return', duration_sec=3) and ok

            if ok:
                self.get_logger().info('Pick/place motion cycle complete; waiting 1.5s')
            else:
                self.get_logger().warn('Cycle had failures; retrying after short pause')
            time.sleep(1.5)


def main():
    rclpy.init()
    node = PickPlaceTrajectoryClient()
    try:
        node.run_loop()
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info('Interrupted, shutting down')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
