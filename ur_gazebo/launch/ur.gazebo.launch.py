#!/usr/bin/env python3
"""
Launch Gazebo simulation with a UR robot.

This launch file sets up a complete ROS 2 simulation environment with Gazebo.

:author: Addison Sears-Collins
:date: November 16, 2024
"""

import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import Command, FindExecutable
from launch_ros.descriptions import ParameterValue

def generate_launch_description():
    """
    Generate a launch description for the Gazebo simulation.
    """
    # Package names
    package_name_gazebo = 'ur_gazebo'
    package_name_description = 'ur_description'
    package_name_moveit = 'movit_config'

    # Default values
    default_robot_name = 'ur'
    default_world_file = 'pick_and_place_demo.world'
    gazebo_models_path = 'models'
    gazebo_worlds_path = 'worlds'
    ros_gz_bridge_config_file_path = 'config/ros_gz_bridge.yaml'

    # Find package paths
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim').find('ros_gz_sim')
    pkg_share_gazebo = FindPackageShare(package_name_gazebo).find(package_name_gazebo)
    pkg_share_description = FindPackageShare(package_name_description).find(package_name_description)
    pkg_share_moveit = FindPackageShare(package_name_moveit).find(package_name_moveit)

    # Set paths
    gazebo_models_path = os.path.join(pkg_share_gazebo, gazebo_models_path)
    default_ros_gz_bridge_config_file_path = os.path.join(pkg_share_gazebo, ros_gz_bridge_config_file_path)

    # Launch Configurations
    world_file = LaunchConfiguration('world_file')
    world_path = PathJoinSubstitution([pkg_share_gazebo, gazebo_worlds_path, world_file])
    
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')

    # Declare launch arguments
    declared_arguments = [
        DeclareLaunchArgument("robot_name", default_value=default_robot_name, description="The name for the robot"),
        DeclareLaunchArgument("use_sim_time", default_value="true", description="Use simulation (Gazebo) clock if true"),
        DeclareLaunchArgument("world_file", default_value=default_world_file, description="World file name"),
        DeclareLaunchArgument("ur_type", default_value="ur5", description="Type/series of UR robot",
                              choices=["ur3", "ur3e", "ur5", "ur5e", "ur10", "ur10e", "ur16e", "ur20", "ur30"]),
        DeclareLaunchArgument("safety_limits", default_value="true", description="Enable safety limits controller"),
        DeclareLaunchArgument("safety_pos_margin", default_value="0.15", description="Safety controller position margin"),
        DeclareLaunchArgument("safety_k_position", default_value="20", description="Safety controller k-position factor"),
        DeclareLaunchArgument("tf_prefix", default_value='""', description="Prefix for joint names"),
    ]

    # Create launch description
    ld = LaunchDescription(declared_arguments)
    
    urdf_xacro_path = os.path.join(pkg_share_description, "urdf", "ur.urdf.xacro")

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]), " ", urdf_xacro_path,
        " safety_limits:=", LaunchConfiguration("safety_limits"),
        " safety_pos_margin:=", LaunchConfiguration("safety_pos_margin"),
        " safety_k_position:=", LaunchConfiguration("safety_k_position"),
        " name:=ur",
        " ur_type:=", LaunchConfiguration("ur_type"),
        " tf_prefix:=", LaunchConfiguration("tf_prefix")
    ])
    robot_description = {'robot_description': ParameterValue(robot_description_content, value_type=str)}

    # Robot State Publisher
    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[robot_description, {'use_sim_time': use_sim_time}]
    )

    # Set environment variables
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        gazebo_models_path
    )

    # Start Gazebo
    start_gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments=[('gz_args', [' -r -v 4 ', world_path])]
    )

    # Start Gazebo ROS Bridge
    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': default_ros_gz_bridge_config_file_path}],
        output='screen'
    )

    # Spawn robot in Gazebo
    start_gazebo_ros_spawner_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/robot_description',
            '-name', robot_name,
            '-allow_renaming', 'true'
        ]
    )

    # Add actions to launch description
    ld.add_action(set_env_vars_resources)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(start_gazebo_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(start_gazebo_ros_spawner_cmd)

    return ld
