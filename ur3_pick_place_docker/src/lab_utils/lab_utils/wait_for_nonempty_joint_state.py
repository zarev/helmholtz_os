#!/usr/bin/env python3

import sys

import rclpy
from rcl_interfaces.msg import ParameterDescriptor
from rclpy.node import Node
from sensor_msgs.msg import JointState


class WaitForNonemptyJointState(Node):
    def __init__(self) -> None:
        super().__init__("wait_for_nonempty_joint_state")
        self.declare_parameter("topic", "/joint_states")
        self.declare_parameter(
            "timeout_sec",
            120.0,
            ParameterDescriptor(dynamic_typing=True),
        )

        self._done = False
        self._success = False
        self._topic = self.get_parameter("topic").get_parameter_value().string_value
        timeout_sec = float(self.get_parameter("timeout_sec").value)

        self.create_subscription(JointState, self._topic, self._on_joint_state, 10)
        self.create_timer(timeout_sec, self._on_timeout)

    def _on_joint_state(self, msg: JointState) -> None:
        if not msg.name or not msg.position:
            return

        self.get_logger().info(
            f"Received non-empty JointState on {self._topic} with {len(msg.name)} joints."
        )
        self._success = True
        self._done = True

    def _on_timeout(self) -> None:
        self.get_logger().error(
            f"Timed out waiting for a non-empty JointState on {self._topic}."
        )
        self._success = False
        self._done = True


def main() -> int:
    rclpy.init()
    node = WaitForNonemptyJointState()

    try:
        while rclpy.ok() and not node._done:
            rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        success = node._success
        node.destroy_node()
        rclpy.shutdown()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
