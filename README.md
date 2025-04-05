# UR Robotic Arm with Robotiq 2-Finger Gripper for ROS2

This project implements the Robotiq 2-Finger Gripper along with the UR robotic arm using ROS2 (Jazzy). It includes the URDF model and launch files necessary for visualizing both the gripper and the robotic arm in RViz.

## Installation

To set up this project, ensure you have ROS2 (Jazzy) installed on your system.

1. Clone the repository:
   ```bash
   git clone https://github.com/darshmenon/
   cd UR3_ROS2_PICK_AND_PLACE
   ```

2. Install the necessary dependencies:
   ```bash
   sudo apt install ros-jazzy-rviz2 \
                    ros-jazzy-joint-state-publisher \
                    ros-jazzy-robot-state-publisher \
                    ros-jazzy-ros2-control \
                    ros-jazzy-ros2-controllers \
                    ros-jazzy-controller-manager \
                    ros-jazzy-joint-trajectory-controller \
                    ros-jazzy-position-controllers \
                    ros-jazzy-gz-ros2-control \
                    ros-jazzy-ros2controlcli
   ```

3. Build your ROS2 workspace:
   ```bash
   cd ~/your_ros2_workspace  # Replace with your workspace path
   colcon build --symlink-install
   source install/setup.bash
   ```

## Usage

This project includes a UR robotic arm with the Robotiq 2-Finger Gripper that can be used for various robotic applications. The URDF models are located in the `urdf` directory, and you can modify them according to your needs.

## Launching Gazebo

To launch Gazebo with the UR robotic arm and the Robotiq 2-Finger Gripper, use the following command:

```bash
ros2 launch 
```

## Launching the Visualization

To visualize the Robotiq 2-Finger Gripper in RViz, use the following command:

```bash
ros2 launch robotiq_2finger_grippers robotiq_2f_85_gripper_visualization/launch/test_2f_85_model.launch.py
```

To visualize the UR robotic arm with the gripper, use:
```bash
ros2 launch ur_description view_ur.launch.py ur_type:=ur3
```



## Screenshots

### Arm with Gripper in RViz
![Arm with Gripper](/images/arm_with_gripper.png)

### Robotiq Gripper Close-up
![Gripper](/images/gripper.png)

### Full Setup in Gazebo
![Gazebo View](/images/image.png)

### RViz View
![RViz 1](/images/rviz1.png)

## Contributing

Contributions are welcome! Please feel free to submit a pull request or create an issue if you find any bugs or have suggestions for improvement.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

