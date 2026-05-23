import os
from glob import glob
from setuptools import setup

PACKAGE_NAME = 'vision_bridge'

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
    description='ROS 2 ↔ OpenCV image bridge — reusable vision foundation',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = vision_bridge.camera_node:main',
        ],
    },
)
