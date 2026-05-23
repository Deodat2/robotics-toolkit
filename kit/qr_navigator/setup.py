import os
from glob import glob
from setuptools import setup

PACKAGE_NAME = 'qr_navigator'

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
        (os.path.join('share', PACKAGE_NAME, 'test_images'),
            glob('test_images/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kossi',
    maintainer_email='ton@email.com',
    description='QR code detection and warehouse localization — reusable',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'qr_detector = qr_navigator.qr_detector:main',
            'waypoint_manager = qr_navigator.waypoint_manager:main',
        ],
    },
)
