#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState


class RobotiqJointStatePublisher(Node):
    def __init__(self) -> None:
        super().__init__("robotiq_joint_state_publisher")
        self.declare_parameter("joint_name", "gripper_robotiq_85_left_knuckle_joint")
        self.declare_parameter("position", 0.0)
        self.declare_parameter("rate_hz", 10.0)

        joint_name = self.get_parameter("joint_name").get_parameter_value().string_value
        position = self.get_parameter("position").get_parameter_value().double_value
        rate_hz = self.get_parameter("rate_hz").get_parameter_value().double_value

        self._joint_name = joint_name
        self._position = position
        self._publisher = self.create_publisher(JointState, "/joint_states", 10)
        self._timer = self.create_timer(1.0 / max(rate_hz, 1.0), self._publish_joint_state)

    def _publish_joint_state(self) -> None:
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [self._joint_name]
        msg.position = [self._position]
        self._publisher.publish(msg)


def main() -> None:
    rclpy.init()
    node = RobotiqJointStatePublisher()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
