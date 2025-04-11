#!/usr/bin/env python3

"""
Pick-and-place using IK and action clients only (no MoveIt Commander).

Author: Darsh Menon
Date: April 11, 2025
"""

import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory, GripperCommand
from trajectory_msgs.msg import JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import PoseStamped

# ⬇️ Replace this with your own IK service or logic
def fake_inverse_kinematics(pose: PoseStamped) -> list:
    """Stub for inverse kinematics. Replace with real IK service or solver."""
    # Replace this with a call to your IK service node (e.g. MoveIt IK, TracIK, or custom)
    # This is just a dummy to mimic some changing values for demonstration
    x, y, z = pose.pose.position.x, pose.pose.position.y, pose.pose.position.z
    return [x, -y, z, 0.0, 1.57, 0.0]  # Dummy joint positions


class IKPickPlaceController(Node):
    def __init__(self):
        super().__init__('ik_pick_place_controller')

        self.arm_client = ActionClient(self, FollowJointTrajectory, '/arm_controller/follow_joint_trajectory')
        self.gripper_client = ActionClient(self, GripperCommand, '/gripper_controller/gripper_cmd')

        self.get_logger().info('Waiting for action servers...')
        self.arm_client.wait_for_server()
        self.gripper_client.wait_for_server()
        self.get_logger().info('Action servers connected!')

        self.joint_names = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint"
        ]

        self.run_pick_place_cycle()

    def create_pose(self, x, y, z):
        pose = PoseStamped()
        pose.header.frame_id = 'base_link'
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0
        return pose

    def send_arm_command(self, joint_positions):
        goal_msg = FollowJointTrajectory.Goal()
        point = JointTrajectoryPoint()
        point.positions = joint_positions
        point.time_from_start = Duration(sec=2)
        goal_msg.trajectory.joint_names = self.joint_names
        goal_msg.trajectory.points = [point]
        self.arm_client.send_goal_async(goal_msg)
        time.sleep(2.5)

    def send_gripper_command(self, position):
        goal_msg = GripperCommand.Goal()
        goal_msg.command.position = position
        goal_msg.command.max_effort = 40.0
        self.gripper_client.send_goal_async(goal_msg)
        time.sleep(1.0)

    def run_pick_place_cycle(self):
        while rclpy.ok():
            # 1. Approach pose (above object)
            approach_pose = self.create_pose(0.22, 0.12, 0.375)
            approach_joints = fake_inverse_kinematics(approach_pose)
            self.get_logger().info('Moving to approach pose')
            self.send_arm_command(approach_joints)

            # 2. Grasp pose (at object)
            grasp_pose = self.create_pose(0.22, 0.12, 0.175)
            grasp_joints = fake_inverse_kinematics(grasp_pose)
            self.get_logger().info('Moving to grasp pose')
            self.send_arm_command(grasp_joints)

            # 3. Close gripper
            self.get_logger().info('Closing gripper')
            self.send_gripper_command(0.8)

            # 4. Retreat
            self.get_logger().info('Retreating to approach pose')
            self.send_arm_command(approach_joints)

            # 5. Move to drop location
            drop_pose = self.create_pose(0.10, -0.25, 0.375)
            drop_joints = fake_inverse_kinematics(drop_pose)
            self.get_logger().info('Moving to drop location')
            self.send_arm_command(drop_joints)

            # 6. Open gripper
            self.get_logger().info('Opening gripper')
            self.send_gripper_command(0.0)

            # 7. Return to home
            home_joints = [0.0] * 6
            self.get_logger().info('Returning to home position')
            self.send_arm_command(home_joints)

            # Done
            self.get_logger().info('Pick-and-place complete. Waiting 2 seconds...')
            time.sleep(2.0)


def main(args=None):
    rclpy.init(args=args)
    node = IKPickPlaceController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
