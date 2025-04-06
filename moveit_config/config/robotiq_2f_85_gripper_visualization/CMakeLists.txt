cmake_minimum_required(VERSION 3.5)
project(robotiq_2f_85_gripper_visualization)

find_package(ament_cmake REQUIRED)

# Install meshes, URDF, and launch files
install(DIRECTORY meshes
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY urdf
  DESTINATION share/${PROJECT_NAME}
)

install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)
install(FILES visualize.rviz
  DESTINATION share/${PROJECT_NAME}
)

# Export package
ament_package()
