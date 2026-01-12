import math

import rclpy
from geometry_msgs.msg import Pose2D
from rclpy.node import Node
from std_msgs.msg import String


class MinimalSimNode(Node):
    """Simple 2D pose integrator that publishes a circular trajectory."""

    def __init__(self) -> None:
        super().__init__("minimal_sim")
        self._pose_pub = self.create_publisher(Pose2D, "sim/pose", 10)
        self._status_pub = self.create_publisher(String, "sim/status", 10)
        self._dt = 0.1
        self._time = 0.0
        self._angular_speed = 0.5  # rad/s
        self._radius = 1.0

        self.create_timer(self._dt, self._step)
        self.create_timer(1.0, self._heartbeat)
        self.get_logger().info(
            "Publishing sim/pose at 10 Hz and sim/status at 1 Hz"
        )

    def _step(self) -> None:
        self._time += self._dt
        pose = Pose2D()
        angle = self._angular_speed * self._time
        pose.x = self._radius * math.cos(angle)
        pose.y = self._radius * math.sin(angle)
        pose.theta = angle
        self._pose_pub.publish(pose)

    def _heartbeat(self) -> None:
        msg = String()
        msg.data = f"sim_time={self._time:.1f}s"
        self._status_pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = MinimalSimNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
