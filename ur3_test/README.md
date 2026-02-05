## Run the robot arm loop simulation with gazebo and moveit

`source install/setup.setup`

### Run the following commands in separate terminals
`ros2 launch ur_gazebo ur.gazebo.launch.py`

`ros2 launch moveit_config move_group.launch.py`

`python3 /ws/src/UR3_ROS2_PICK_AND_PLACE/ur_system_tests/scripts/arm_gripper_loop_controller.py`

