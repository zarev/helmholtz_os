cmake_minimum_required(VERSION 3.5)
project(robotiq_2f_85_gripper_visualization)

find_package(ament_cmake REQUIRED)
find_package(urdf REQUIRED)
find_package(xacro REQUIRED)
find_package(robot_state_publisher REQUIRED)
find_package(joint_state_publisher_gui REQUIRED)
find_package(rviz2 REQUIRED)

# Install meshes and URDF files
install(DIRECTORY meshes DESTINATION share/${PROJECT_NAME})
install(DIRECTORY urdf DESTINATION share/${PROJECT_NAME})

ament_package()
