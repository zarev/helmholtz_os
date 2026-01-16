from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="minimal_sim",
                executable="sim_loop",
                name="minimal_sim",
                output="screen",
            )
        ]
    )
