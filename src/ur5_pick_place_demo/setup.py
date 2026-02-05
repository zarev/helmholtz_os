from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ur5_pick_place_demo'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.xacro')),
        (os.path.join('share', package_name, 'urdf/macros'), glob('urdf/macros/*.xacro')),
        (os.path.join('share', package_name, 'urdf/sensors'), glob('urdf/sensors/*.xacro')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
        (os.path.join('share', package_name, 'action'), glob('action/*.action')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='UR5e Pick and Place Demo for ROS 2 Jazzy',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pick_place_server = ur5_pick_place_demo.pick_place_action_server:main',
            'motion_planner = ur5_pick_place_demo.motion_planner:main',
            'gripper_interface = ur5_pick_place_demo.gripper_interface:main',
            'pick_place_demo_node = ur5_pick_place_demo.pick_place_demo_node:main',
        ],
    },
)