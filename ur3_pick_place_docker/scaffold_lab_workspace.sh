#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="${ROOT_DIR}/src"
FACTORY_DIR="${SRC_DIR}/factory"
GAZEBO_PKG="${SRC_DIR}/lab_robot_gazebo"

declare -A PKG_TYPE=(
  [lab_robot_description]=ament_cmake
  [lab_robot_gazebo]=ament_cmake
  [lab_robot_control]=ament_cmake
  [lab_robot_bringup]=ament_python
  [lab_robot_moveit_config]=ament_cmake
  [lab_navigation]=ament_cmake
  [lab_manipulation]=ament_cmake
  [lab_perception]=ament_cmake
  [lab_vision_interfaces]=interface
  [lab_task_planning]=ament_python
  [lab_workcell_manager]=ament_python
  [lab_scene_manager]=ament_python
  [lab_digital_twin]=ament_python
  [lab_inventory_manager]=ament_python
  [lab_sample_tracking]=ament_python
  [lab_device_interfaces]=interface
  [lab_instrument_drivers]=ament_cmake
  [lab_protocol_executor]=ament_python
  [lab_scheduler]=ament_python
  [lab_state_machine]=ament_python
  [lab_safety_system]=ament_cmake
  [lab_monitoring]=ament_python
  [lab_logging]=ament_python
  [lab_data_manager]=ament_python
  [lab_hmi]=ament_python
  [lab_remote_ops]=ament_python
  [lab_msgs]=interface
  [lab_utils]=ament_python
  [lab_tests]=ament_cmake
  [lab_benchmarks]=ament_cmake
  [lab_demo_tasks]=ament_python
  [third_party]=ament_cmake
)

declare -A PKG_DIRS=(
  [lab_robot_description]="urdf xacro meshes rviz launch config"
  [lab_robot_gazebo]="worlds models plugins launch config"
  [lab_robot_control]="config launch src include/lab_robot_control"
  [lab_robot_bringup]="config launch"
  [lab_robot_moveit_config]="config launch srdf rviz"
  [lab_navigation]="config launch maps behavior_trees src include/lab_navigation"
  [lab_manipulation]="config launch grasp_profiles src include/lab_manipulation"
  [lab_perception]="config launch models src include/lab_perception"
  [lab_vision_interfaces]="msg srv action"
  [lab_task_planning]="workflows plans behavior_trees config launch"
  [lab_workcell_manager]="config launch workcells"
  [lab_scene_manager]="config launch scenes"
  [lab_digital_twin]="config launch models sync"
  [lab_inventory_manager]="database schemas config launch"
  [lab_sample_tracking]="database schemas config launch"
  [lab_device_interfaces]="msg srv action"
  [lab_instrument_drivers]="drivers config launch src include/lab_instrument_drivers"
  [lab_protocol_executor]="workflows plans behavior_trees config launch"
  [lab_scheduler]="workflows plans behavior_trees config launch"
  [lab_state_machine]="workflows plans behavior_trees config launch"
  [lab_safety_system]="config launch policies src include/lab_safety_system"
  [lab_monitoring]="dashboards alerts logs config launch"
  [lab_logging]="pipelines logs config launch"
  [lab_data_manager]="database schemas config launch"
  [lab_hmi]="ui config launch"
  [lab_remote_ops]="clients config launch"
  [lab_msgs]="msg srv action"
  [lab_utils]="scripts config launch"
  [lab_tests]="test fixtures config launch"
  [lab_benchmarks]="scenarios config launch src include/lab_benchmarks"
  [lab_demo_tasks]="workflows plans behavior_trees config launch demos"
  [third_party]="vendor patches cmake"
)

write_file() {
  local path="$1"
  shift
  mkdir -p "$(dirname "${path}")"
  cat > "${path}" <<EOF
$*
EOF
}

write_comment_file() {
  local path="$1"
  local text="$2"
  mkdir -p "$(dirname "${path}")"
  printf '%s\n' "${text}" > "${path}"
}

create_ament_cmake_package() {
  local pkg="$1"
  local pkg_dir="${SRC_DIR}/${pkg}"

  write_file "${pkg_dir}/package.xml" "<?xml version=\"1.0\"?>
<package format=\"3\">
  <name>${pkg}</name>
  <version>0.0.1</version>
  <description>Scaffold package for ${pkg}.</description>
  <maintainer email=\"lab@example.com\">Lab Scaffold</maintainer>
  <license>Apache-2.0</license>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>"

  write_file "${pkg_dir}/CMakeLists.txt" "cmake_minimum_required(VERSION 3.8)
project(${pkg})

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  .
  DESTINATION share/\${PROJECT_NAME}
  USE_SOURCE_PERMISSIONS
  FILES_MATCHING
  PATTERN \"*.launch.py\"
  PATTERN \"*.yaml\"
  PATTERN \"*.xml\"
  PATTERN \"*.rviz\"
  PATTERN \"*.xacro\"
  PATTERN \"*.urdf\"
  PATTERN \"*.sdf\"
  PATTERN \"*.world\"
  PATTERN \"*.sql\"
  PATTERN \"*.json\"
  PATTERN \"*.ui\"
  PATTERN \"*.md\"
  PATTERN \"*.hpp\"
  PATTERN \"*.cpp\"
  PATTERN \"*.msg\"
  PATTERN \"*.srv\"
  PATTERN \"*.action\"
)

ament_package()"

  write_comment_file "${pkg_dir}/README.md" "# ${pkg}"
}

create_ament_python_package() {
  local pkg="$1"
  local pkg_dir="${SRC_DIR}/${pkg}"

  mkdir -p "${pkg_dir}/resource" "${pkg_dir}/${pkg}"

  write_file "${pkg_dir}/package.xml" "<?xml version=\"1.0\"?>
<package format=\"3\">
  <name>${pkg}</name>
  <version>0.0.1</version>
  <description>Scaffold package for ${pkg}.</description>
  <maintainer email=\"lab@example.com\">Lab Scaffold</maintainer>
  <license>Apache-2.0</license>
  <buildtool_depend>ament_python</buildtool_depend>
  <exec_depend>rclpy</exec_depend>
  <export>
    <build_type>ament_python</build_type>
  </export>
</package>"

  write_file "${pkg_dir}/setup.py" "from setuptools import find_packages, setup

package_name = '${pkg}'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Lab Scaffold',
    maintainer_email='lab@example.com',
    description='Scaffold package for ${pkg}.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': []},
)"

  write_file "${pkg_dir}/setup.cfg" "[develop]
script_dir=\$base/lib/${pkg}
[install]
install_scripts=\$base/lib/${pkg}"

  write_comment_file "${pkg_dir}/resource/${pkg}" "# resource marker"
  write_comment_file "${pkg_dir}/${pkg}/__init__.py" "\"\"\"${pkg} scaffold package.\"\"\""
  write_comment_file "${pkg_dir}/${pkg}/placeholder.py" "\"\"\"Placeholder module for ${pkg}.\"\"\""
  write_comment_file "${pkg_dir}/README.md" "# ${pkg}"
}

create_interface_package() {
  local pkg="$1"
  local pkg_dir="${SRC_DIR}/${pkg}"

  write_file "${pkg_dir}/package.xml" "<?xml version=\"1.0\"?>
<package format=\"3\">
  <name>${pkg}</name>
  <version>0.0.1</version>
  <description>Interface scaffold package for ${pkg}.</description>
  <maintainer email=\"lab@example.com\">Lab Scaffold</maintainer>
  <license>Apache-2.0</license>
  <buildtool_depend>ament_cmake</buildtool_depend>
  <buildtool_depend>rosidl_default_generators</buildtool_depend>
  <depend>builtin_interfaces</depend>
  <depend>geometry_msgs</depend>
  <exec_depend>rosidl_default_runtime</exec_depend>
  <member_of_group>rosidl_interface_packages</member_of_group>
  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>"

  write_file "${pkg_dir}/CMakeLists.txt" "cmake_minimum_required(VERSION 3.8)
project(${pkg})

find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(\${PROJECT_NAME}
  \"msg/Placeholder.msg\"
  \"srv/Placeholder.srv\"
  \"action/Placeholder.action\"
  DEPENDENCIES builtin_interfaces geometry_msgs
)

ament_export_dependencies(rosidl_default_runtime)
ament_package()"

  write_file "${pkg_dir}/msg/Placeholder.msg" "# Placeholder message
string name
builtin_interfaces/Time stamp"

  write_file "${pkg_dir}/srv/Placeholder.srv" "# Placeholder service request
string name
---
# Placeholder service response
bool accepted"

  write_file "${pkg_dir}/action/Placeholder.action" "# Placeholder action goal
string goal_name
---
# Placeholder action result
bool success
---
# Placeholder action feedback
string state"

  write_comment_file "${pkg_dir}/README.md" "# ${pkg}"
}

create_dir_placeholders() {
  local pkg="$1"
  local pkg_dir="${SRC_DIR}/${pkg}"

  for dir_name in ${PKG_DIRS[${pkg}]}; do
    mkdir -p "${pkg_dir}/${dir_name}"
    case "${dir_name}" in
      config)
        write_comment_file "${pkg_dir}/${dir_name}/${pkg}.yaml" "# ${pkg} configuration placeholder"
        ;;
      launch)
        write_comment_file "${pkg_dir}/${dir_name}/${pkg}.launch.py" "# ${pkg} launch placeholder"
        ;;
      urdf)
        write_comment_file "${pkg_dir}/${dir_name}/lab_robot.urdf.xacro" "<!-- lab robot urdf placeholder -->"
        ;;
      xacro)
        write_comment_file "${pkg_dir}/${dir_name}/sensors.xacro" "<!-- lab robot xacro placeholder -->"
        ;;
      meshes)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# mesh placeholders"
        ;;
      rviz)
        write_comment_file "${pkg_dir}/${dir_name}/default.rviz" "# rviz placeholder"
        ;;
      worlds)
        write_comment_file "${pkg_dir}/${dir_name}/empty_lab.sdf" "<!-- gazebo world placeholder -->"
        ;;
      models)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# model placeholders"
        ;;
      plugins)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# plugin placeholders"
        ;;
      src)
        write_comment_file "${pkg_dir}/${dir_name}/placeholder.cpp" "// ${pkg} source placeholder"
        ;;
      include/*)
        write_comment_file "${pkg_dir}/${dir_name}/placeholder.hpp" "// ${pkg} header placeholder"
        ;;
      behavior_trees)
        write_comment_file "${pkg_dir}/${dir_name}/default_tree.xml" "<!-- behavior tree placeholder -->"
        ;;
      workflows)
        write_comment_file "${pkg_dir}/${dir_name}/default_workflow.yaml" "# workflow placeholder"
        ;;
      plans)
        write_comment_file "${pkg_dir}/${dir_name}/default.plan.yaml" "# plan placeholder"
        ;;
      maps)
        write_comment_file "${pkg_dir}/${dir_name}/facility_map.yaml" "# map placeholder"
        ;;
      grasp_profiles)
        write_comment_file "${pkg_dir}/${dir_name}/default_grasp.yaml" "# grasp profile placeholder"
        ;;
      database)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "-- database placeholder"
        ;;
      schemas)
        write_comment_file "${pkg_dir}/${dir_name}/schema.sql" "-- schema placeholder"
        ;;
      dashboards)
        write_comment_file "${pkg_dir}/${dir_name}/overview.json" "{ \"placeholder\": true }"
        ;;
      alerts)
        write_comment_file "${pkg_dir}/${dir_name}/alert_rules.yaml" "# alert rules placeholder"
        ;;
      logs)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# log placeholder"
        ;;
      drivers)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# driver placeholder"
        ;;
      ui)
        write_comment_file "${pkg_dir}/${dir_name}/main_window.ui" "<!-- hmi ui placeholder -->"
        ;;
      clients)
        write_comment_file "${pkg_dir}/${dir_name}/remote_client.yaml" "# remote client placeholder"
        ;;
      workcells)
        write_comment_file "${pkg_dir}/${dir_name}/main_workcell.yaml" "# workcell placeholder"
        ;;
      scenes)
        write_comment_file "${pkg_dir}/${dir_name}/default_scene.yaml" "# scene placeholder"
        ;;
      sync)
        write_comment_file "${pkg_dir}/${dir_name}/sync_rules.yaml" "# digital twin sync placeholder"
        ;;
      scripts)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# utility script placeholder"
        ;;
      policies)
        write_comment_file "${pkg_dir}/${dir_name}/safety_policy.yaml" "# safety policy placeholder"
        ;;
      test)
        write_comment_file "${pkg_dir}/${dir_name}/test_placeholder.py" "# test placeholder"
        ;;
      fixtures)
        write_comment_file "${pkg_dir}/${dir_name}/sample_fixture.yaml" "# fixture placeholder"
        ;;
      scenarios)
        write_comment_file "${pkg_dir}/${dir_name}/baseline.yaml" "# benchmark scenario placeholder"
        ;;
      demos)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# demo placeholder"
        ;;
      vendor)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# vendor dependency placeholder"
        ;;
      patches)
        write_comment_file "${pkg_dir}/${dir_name}/README.md" "# patch placeholder"
        ;;
      cmake)
        write_comment_file "${pkg_dir}/${dir_name}/Dependencies.cmake" "# dependency placeholder"
        ;;
    esac
  done
}

copy_factory_world() {
  mkdir -p "${GAZEBO_PKG}/worlds" "${GAZEBO_PKG}/models"

  if [[ -f "${FACTORY_DIR}/factory.model" ]]; then
    cp "${FACTORY_DIR}/factory.model" "${GAZEBO_PKG}/worlds/lab_factory.sdf"
  fi

  if [[ -d "${FACTORY_DIR}/models" ]]; then
    cp -r "${FACTORY_DIR}/models/." "${GAZEBO_PKG}/models/"
  fi
}

mkdir -p "${SRC_DIR}"

for pkg in "${!PKG_TYPE[@]}"; do
  mkdir -p "${SRC_DIR}/${pkg}"
  case "${PKG_TYPE[${pkg}]}" in
    ament_cmake)
      create_ament_cmake_package "${pkg}"
      ;;
    ament_python)
      create_ament_python_package "${pkg}"
      ;;
    interface)
      create_interface_package "${pkg}"
      ;;
  esac
  create_dir_placeholders "${pkg}"
done

copy_factory_world

write_comment_file "${SRC_DIR}/README.md" "# ROS 2 lab automation workspace scaffold"
