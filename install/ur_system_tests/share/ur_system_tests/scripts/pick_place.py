#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from moveit_py.robot_trajectory import RobotTrajectory
from moveit_py.planning_scene_monitor import PlanningSceneMonitor
from moveit_py.core import RobotModel
from moveit_py.planning_interface import MoveGroupInterface

class PickPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_place_node')

        # Load MoveGroup interface
        self.move_group = MoveGroupInterface(
            group_name="manipulator",  # Adjust this if your planning group is different
            node=self
        )
        self.move_group.set_planning_time(5.0)
        self.move_group.set_max_velocity_scaling_factor(0.5)
        self.move_group.set_max_acceleration_scaling_factor(0.5)

        # Setup planning scene monitor
        self.scene_monitor = PlanningSceneMonitor("robot_description")
        self.scene_monitor.start_state_monitor()
        self.scene_monitor.start_scene_monitor()
        self.scene_monitor.start_world_geometry_monitor()

        self.get_logger().info("MoveIt PickPlaceNode initialized.")
        self.run_pick_place()

    def run_pick_place(self):
        # Move to home position
        self.get_logger().info("Moving to home position...")
        self.move_group.set_named_target("home")
        success = self.move_group.go(wait=True)
        self.move_group.stop()
        self.get_logger().info(f"Moved to home: {success}")

        # Define a pick pose
        pick_pose = PoseStamped()
        pick_pose.header.frame_id = "base_link"
        pick_pose.pose.position.x = 0.4
        pick_pose.pose.position.y = 0.0
        pick_pose.pose.position.z = 0.2
        pick_pose.pose.orientation.w = 1.0

        self.move_group.set_pose_target(pick_pose)

        self.get_logger().info("Planning to pick pose...")
        success = self.move_group.go(wait=True)
        self.move_group.stop()
        self.move_group.clear_pose_targets()
        self.get_logger().info(f"Pick move success: {success}")

        # Simulate gripping here if needed

        # Define a place pose
        place_pose = PoseStamped()
        place_pose.header.frame_id = "base_link"
        place_pose.pose.position.x = 0.3
        place_pose.pose.position.y = -0.3
        place_pose.pose.position.z = 0.25
        place_pose.pose.orientation.w = 1.0

        self.move_group.set_pose_target(place_pose)

        self.get_logger().info("Planning to place pose...")
        success = self.move_group.go(wait=True)
        self.move_group.stop()
        self.move_group.clear_pose_targets()
        self.get_logger().info(f"Place move success: {success}")

        # Simulate releasing here if needed

def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
