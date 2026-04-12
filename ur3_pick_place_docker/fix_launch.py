import sys

filename = "src/lab_robot_control/launch/ur_with_gripper_sim.launch.py"
with open(filename, "r") as f:
    code = f.read()

if "ParameterValue" not in code:
    code = code.replace(
        "from launch_ros.actions import Node",
        "from launch_ros.actions import Node\nfrom launch_ros.parameter_descriptions import ParameterValue"
    )
    
    # We don't directly invoke xacro here, the description_file parameter 
    # passed to ur_simulation_gz already contains the path to the xacro file.
    # Actually, ur_sim_control.launch.py in ur_simulation_gz takes `description_file` as the *path* to the xacro file,
    # NOT the evaluated xml string. Let me double check ur_simulation_gz.
