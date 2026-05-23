import os
from glob import glob
from setuptools import setup

PACKAGE_NAME = 'amr_ros2_bringup'

setup(
    name=PACKAGE_NAME,
    version='1.0.0',
    packages=[PACKAGE_NAME],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + PACKAGE_NAME]),
        ('share/' + PACKAGE_NAME, ['package.xml']),
        # Launch files
        (os.path.join('share', PACKAGE_NAME, 'launch'),
            glob('launch/*.py')),
        # Gazebo worlds
        (os.path.join('share', PACKAGE_NAME, 'worlds'),
            glob('worlds/*.world')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kossi',
    maintainer_email='ton@email.com',
    description='AMR ROS 2 project bringup — master launch file',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={'console_scripts': []},
)