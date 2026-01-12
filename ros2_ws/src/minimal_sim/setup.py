from setuptools import setup

package_name = "minimal_sim"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/launch", ["launch/sim_launch.py"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Helmholtz OS",
    maintainer_email="dev@helmholtz.local",
    description="Minimal ROS 2 simulation loop publishing pose and status topics.",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "sim_loop=minimal_sim.sim_loop:main",
        ],
    },
)
