import sys

filename = "src/lab_robot_control/launch/ur_with_gripper_sim.launch.py"
with open(filename, "r") as f:
    code = f.read()

if "ParameterValue" not in code:
    code = code.replace(
        "from launch_ros.actions import Node",
        "from launch_ros.actions import Node\nfrom launch_ros.parameter_descriptions import ParameterValue"
    )
