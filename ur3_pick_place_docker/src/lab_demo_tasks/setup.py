from setuptools import find_packages, setup

package_name = 'lab_demo_tasks'

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
    description='Scaffold package for lab_demo_tasks.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'pick_place_moveit_action = lab_demo_tasks.pick_place_moveit_action:main',
        ],
    },
)
