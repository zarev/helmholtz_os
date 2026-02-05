import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

from .moveit import MoveItInterface
from . import scene_objects as so

class PickPlaceDemo(Node):
    def __init__(self):
        super().__init__("ur5_pick_place_demo")

        self.attach_pub = self.create_publisher(Bool, "/attach_box", 10)
        self.detach_pub = self.create_publisher(Bool, "/detach_box", 10)

        self.moveit = MoveItInterface(self)

    def _wait_bridge(self):
        while self.attach_pub.get_subscription_count() == 0 or self.detach_pub.get_subscription_count() == 0:
            self.get_logger().info("Waiting for /attach_box and /detach_box bridge subscribers...")
            rclpy.spin_once(self, timeout_sec=0.2)

    def _publish(self, pub):
        msg = Bool()
        msg.data = True
        pub.publish(msg)

    def run(self):
        self.get_logger().info("Waiting for MoveIt...")
        self.moveit.wait_ready()

        self.get_logger().info("Waiting for Gazebo bridge subscribers...")
        self._wait_bridge()

        time.sleep(1.0)

        self.get_logger().info("Pregrasp")
        self.moveit.move_to_pose(*so.PREGRASP.__dict__.values())

        self.get_logger().info("Grasp")
        self.moveit.move_to_pose(*so.GRASP.__dict__.values())

        self.get_logger().info("Attach (close gripper)")
        self._publish(self.attach_pub)
        time.sleep(0.5)

        self.get_logger().info("Lift")
        self.moveit.move_to_pose(*so.LIFT.__dict__.values())

        self.get_logger().info("Preplace")
        self.moveit.move_to_pose(*so.PREPLACE.__dict__.values())

        self.get_logger().info("Place")
        self.moveit.move_to_pose(*so.PLACE.__dict__.values())

        self.get_logger().info("Detach (open gripper)")
        self._publish(self.detach_pub)
        time.sleep(0.5)

        self.get_logger().info("Retreat")
        self.moveit.move_to_pose(*so.RETREAT.__dict__.values())

        self.get_logger().info("Done")

def main():
    rclpy.init()
    node = PickPlaceDemo()
    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()
