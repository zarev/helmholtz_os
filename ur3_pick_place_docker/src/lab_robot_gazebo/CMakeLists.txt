cmake_minimum_required(VERSION 3.8)
project(lab_robot_gazebo)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  .
  DESTINATION share/${PROJECT_NAME}
  USE_SOURCE_PERMISSIONS
  FILES_MATCHING
  PATTERN "*.launch.py"
  PATTERN "*.yaml"
  PATTERN "*.xml"
  PATTERN "*.rviz"
  PATTERN "*.xacro"
  PATTERN "*.urdf"
  PATTERN "*.sdf"
  PATTERN "*.world"
  PATTERN "*.sql"
  PATTERN "*.json"
  PATTERN "*.ui"
  PATTERN "*.md"
  PATTERN "*.hpp"
  PATTERN "*.cpp"
  PATTERN "*.msg"
  PATTERN "*.srv"
  PATTERN "*.action"
)

ament_package()
