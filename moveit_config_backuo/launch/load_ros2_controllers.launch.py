#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():
    """Launch robot controllers in a defined sequence."""

    # Start joint state broadcaster immediately
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen'
    )

    # Start arm controller after short delay
    arm_controller_spawner = TimerAction(
        period=2.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['arm_controller'],
            output='screen'
        )]
    )

    # Start gripper controller after arm controller
    grip_controller_spawner = TimerAction(
        period=4.0,
        actions=[Node(
            package='controller_manager',
            executable='spawner',
            arguments=['grip_action_controller'],
            output='screen'
        )]
    )

    ld = LaunchDescription()
    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(arm_controller_spawner)
    ld.add_action(grip_controller_spawner)

    return ld
