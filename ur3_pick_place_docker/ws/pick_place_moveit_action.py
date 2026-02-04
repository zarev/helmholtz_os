#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from moveit_msgs.action import MoveGroup
from geometry_msgs.msg import PoseStamped


class MoveItPoseClient(Node):
    def __init__(self):
        super().__init__('moveit_pose_client')

        self.client = ActionClient(self, MoveGroup, '/move_action')
        self.get_logger().info('Waiting for MoveIt action server...')
        self.client.wait_for_server()
        self.get_logger().info('Connected to MoveIt')

        self.send_pose_goal()

    def send_pose_goal(self):
        goal = MoveGroup.Goal()

        goal.request.group_name = 'ur_manipulator'
        goal.request.num_planning_attempts = 5
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = 0.3
        goal.request.max_acceleration_scaling_factor = 0.3

        pose = PoseStamped()
        pose.header.frame_id = 'base_link'
        pose.pose.position.x = 0.22
        pose.pose.position.y = 0.12
        pose.pose.position.z = 0.30
        pose.pose.orientation.w = 1.0

        goal.request.goal_constraints.append(
            self.pose_to_constraint(pose)
        )

        self.client.send_goal_async(goal)

    def pose_to_constraint(self, pose):
        from moveit_msgs.msg import Constraints, PositionConstraint, OrientationConstraint
        from shape_msgs.msg import SolidPrimitive

        c = Constraints()

        pc = PositionConstraint()
        pc.header = pose.header
        pc.link_name = 'tool0'
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [0.01, 0.01, 0.01]
        pc.constraint_region.primitives.append(box)
        pc.constraint_region.primitive_poses.append(pose.pose)
        pc.weight = 1.0

        oc = OrientationConstraint()
        oc.header = pose.header
        oc.link_name = 'tool0'
        oc.orientation = pose.pose.orientation
        oc.absolute_x_axis_tolerance = 0.1
        oc.absolute_y_axis_tolerance = 0.1
        oc.absolute_z_axis_tolerance = 0.1
        oc.weight = 1.0

        c.position_constraints.append(pc)
        c.orientation_constraints.append(oc)

        return c


def main():
    rclpy.init()
    node = MoveItPoseClient()
    rclpy.spin(node)


if __name__ == '__main__':
    main()
