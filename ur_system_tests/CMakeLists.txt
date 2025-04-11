cmake_minimum_required(VERSION 3.8)
project(ur_system_tests)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find required packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_action REQUIRED)
find_package(control_msgs REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(moveit_common REQUIRED)
find_package(moveit_core REQUIRED)
find_package(pluginlib REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

# -------------------- Executables --------------------

add_executable(arm_gripper_loop_controller src/arm_gripper_loop_controller.cpp)
ament_target_dependencies(arm_gripper_loop_controller
  rclcpp rclcpp_action control_msgs)

add_executable(test_pick_and_place src/test_pick_and_place.cpp)
ament_target_dependencies(test_pick_and_place
 control_msgs rclcpp rclcpp_action moveit_ros_planning_interface)

# Add more test files if needed
add_executable(test_send_joint_space_goal src/test_send_joint_space_goal.cpp)
ament_target_dependencies(test_send_joint_space_goal
  rclcpp moveit_ros_planning_interface)

# -------------------- Installation --------------------

# Install cpp executables
install(TARGETS
  arm_gripper_loop_controller
  test_pick_and_place
  test_send_joint_space_goal
  DESTINATION lib/${PROJECT_NAME}
)

# Install Python executables
install(PROGRAMS
  scripts/arm_gripper_loop_controller.py
  scripts/pick_place.py
  DESTINATION lib/${PROJECT_NAME}
)

# Optional: install scripts & source for convenience
install(DIRECTORY
  scripts
  src
  DESTINATION share/${PROJECT_NAME}
)

# -------------------- Lint & Package --------------------

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
