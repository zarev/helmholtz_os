import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/darsh/UR3_ROS2_PICK_AND_PLACE/install/joint_state_publisher'
