import os
from glob import glob
from setuptools import setup

PACKAGE_NAME = 'sensor_interface'

setup(
    name=PACKAGE_NAME,
    version='0.1.0',
    packages=[PACKAGE_NAME],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + PACKAGE_NAME]),
        ('share/' + PACKAGE_NAME, ['package.xml']),
        (os.path.join('share', PACKAGE_NAME, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', PACKAGE_NAME, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kossi',
    maintainer_email='ton@email.com',
    description='Sensor abstraction layer — reusable across ROS 2 projects',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # ros2 run sensor_interface lidar_filter
            'lidar_filter = sensor_interface.lidar_filter:main',
            # ros2 run sensor_interface odom_filter
            'odom_filter  = sensor_interface.odom_filter:main',
        ],
    },
)
