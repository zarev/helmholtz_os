#!/usr/bin/env python3


import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import PoseStamped
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive
from control_msgs.action import GripperCommand
from moveit.planning import MoveItPy, PlanningComponent

class PickPlaceController(Node):
    def __init__(self):
        super().__init__('pick_place_controller')
        
        # Initialize MoveIt with proper configuration
        self.moveit = MoveItPy(
            node_name="moveit_py",
            config_dict={
                "planning_plugin": "ompl_interface/OMPLPlanner",
                "request_adapters": """default_planner_request_adapters/AddTimeOptimalParameterization \
                                    default_planner_request_adapters/FixWorkspaceBounds \
                                    default_planner_request_adapters/FixStartStateBounds \
                                    default_planner_request_adapters/FixStartStateCollision"""
            }
        )
        
        # Create planning components
        self.arm = PlanningComponent("arm", self.moveit)
        self.gripper = PlanningComponent("gripper", self.moveit)
        
        # Gripper action client
        self.gripper_client = ActionClient(
            self, GripperCommand, '/gripper_controller/gripper_cmd')
        
        # Object parameters
        self.cylinder_pose = PoseStamped()
        self.cylinder_pose.header.frame_id = "world"
        self.cylinder_pose.pose.position.x = 0.22
        self.cylinder_pose.pose.position.y = 0.12
        self.cylinder_pose.pose.position.z = 0.175
        self.cylinder_dimensions = [0.35, 0.03]  # [height, radius]
        
        self.initialize_environment()
        self.execute_pick_place_cycle()

    def initialize_environment(self):
        """Add collision objects to planning scene"""
        collision_object = CollisionObject()
        collision_object.id = "target_cylinder"
        collision_object.header.frame_id = "world"
        
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.CYLINDER
        primitive.dimensions = self.cylinder_dimensions
        
        cylinder_pose = self.cylinder_pose.pose
        
        collision_object.primitives.append(primitive)
        collision_object.primitive_poses.append(cylinder_pose)
        collision_object.operation = CollisionObject.ADD
        
        self.moveit.get_planning_scene_monitor().apply_collision_object(collision_object)

    # Rest of the class remains the same as previous version...
    # [Keep the move_gripper, plan_and_execute, execute_pick_place_cycle, and create_pose methods]

def main(args=None):
    rclpy.init(args=args)
    controller = PickPlaceController()
    rclpy.spin(controller)
    controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()