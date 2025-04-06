#!/usr/bin/env python3
"""
Control robot arm and gripper to perform repetitive movements between positions.

Action Clients:
    /arm_controller/follow_joint_trajectory (control_msgs/FollowJointTrajectory)
    /gripper_action_controller/gripper_cmd (control_msgs/GripperCommand)

:author: darsh Menon
:date: March 11, 2025
"""

import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class ArmGripperLoopController(Node):
    def __init__(self):
        super().__init__('arm_gripper_loop_controller')

        # Arm action client
        self.arm_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory'
        )

        # Gripper action client (FIXED name)
        self.gripper_client = ActionClient(
            self,
            GripperCommand,
            '/grip_action_controller/gripper_cmd'
        )

        self.get_logger().info('Waiting for action servers...')
        self.arm_client.wait_for_server()
        self.gripper_client.wait_for_server()
        self.get_logger().info('Action servers connected!')

        # Robot joint names (make sure this matches your URDF/joint list)
        self.joint_names = [
            "elbow_joint", "finger_joint", "shoulder_lift_joint",
            "shoulder_pan_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"
        ]

        # Define poses
        self.target_pos = [1.345, -1.23, 0.264, -0.296, 0.389, -1.5, 0.0]
        self.home_pos = [0.0] * 7

        # Start control loop shortly after startup
        self.create_timer(0.1, self.control_loop_callback)

    def send_arm_command(self, positions: list) -> None:
        point = JointTrajectoryPoint()
        point.positions = positions
        point.time_from_start = Duration(sec=2)

        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        goal_msg.trajectory.points = [point]

        self.arm_client.send_goal_async(goal_msg)

    def send_gripper_command(self, position: float) -> None:
        goal_msg = GripperCommand.Goal()
        goal_msg.command.position = position
        goal_msg.command.max_effort = 5.0

        self.gripper_client.send_goal_async(goal_msg)

    def control_loop_callback(self) -> None:
        self.get_logger().info('Moving to target position')
        self.send_arm_command(self.target_pos)
        time.sleep(2.5)

        self.get_logger().info('Reached target - Closing gripper')
        self.send_gripper_command(-0.7)
        time.sleep(0.5)

        self.get_logger().info('Moving to home position')
        self.send_arm_command(self.home_pos)
        time.sleep(2.5)

        self.get_logger().info('Reached home - Opening gripper')
        self.send_gripper_command(0.0)
        time.sleep(0.5)

        self.get_logger().info('Cycle complete - Waiting before next cycle')
        time.sleep(1.0)


def main(args=None):
    rclpy.init(args=args)
    controller = ArmGripperLoopController()

    try:
        rclpy.spin(controller)
    except KeyboardInterrupt:
        controller.get_logger().info('Shutting down arm gripper controller...')
    finally:
        controller.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
