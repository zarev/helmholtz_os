from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ur_type = LaunchConfiguration("ur_type")
    description_file = LaunchConfiguration("description_file")
    world_file = LaunchConfiguration("world_file")
    controllers_file = LaunchConfiguration("controllers_file")
    launch_rviz = LaunchConfiguration("launch_rviz")
    gazebo_gui = LaunchConfiguration("gazebo_gui")

    declared_arguments = [
        DeclareLaunchArgument("ur_type", default_value="ur3e"),
        DeclareLaunchArgument("description_file"),
        DeclareLaunchArgument("world_file"),
        DeclareLaunchArgument("controllers_file"),
        DeclareLaunchArgument("launch_rviz", default_value="false"),
        DeclareLaunchArgument("gazebo_gui", default_value="true"),
    ]

    ur_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ur_simulation_gz"), "launch", "ur_sim_control.launch.py"]
            )
        ),
        launch_arguments={
            "ur_type": ur_type,
            "description_file": description_file,
            "world_file": world_file,
            "controllers_file": controllers_file,
            "launch_rviz": launch_rviz,
            "gazebo_gui": gazebo_gui,
            "initial_joint_controller": "scaled_joint_trajectory_controller",
        }.items(),
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        output="screen",
    )

    delayed_gripper_spawner = TimerAction(period=8.0, actions=[gripper_controller_spawner])

    return LaunchDescription(declared_arguments + [ur_sim, delayed_gripper_spawner])
