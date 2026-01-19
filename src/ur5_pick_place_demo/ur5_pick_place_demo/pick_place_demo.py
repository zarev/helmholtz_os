#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

class PickPlaceDemo(Node):
    def __init__(self):
        super().__init__('pick_place_demo')
        self.get_logger().info('ur5_pick_place_demo started ✅')

def main():
    rclpy.init()
    node = PickPlaceDemo()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
