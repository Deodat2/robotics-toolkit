import os
from glob import glob
from setuptools import setup

PACKAGE_NAME = 'slam_module'

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
        # maps/ directory included but starts empty
        # actual map files are generated at runtime
        (os.path.join('share', PACKAGE_NAME, 'maps'),
            glob('maps/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kossi',
    maintainer_email='ton@email.com',
    description='SLAM mapping module — reusable across ROS 2 projects',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # ros2 run slam_module map_manager
            'map_manager = slam_module.map_manager:main',
        ],
    },
)
