"""
============================================================
FILE        : object_detector.launch.py
MODULE      : object_detector (kit/)
DESCRIPTION : Launches YOLOv8 object detection node.

DEPENDS ON:
    - robot_base.launch.py      (camera)
    - vision_bridge.launch.py   (preprocessed frames)

STANDALONE:
    ros2 launch object_detector object_detector.launch.py
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('object_detector')
    params_file = os.path.join(pkg, 'config', 'detector_params.yaml')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )

    yolo_node = Node(
        package='object_detector',
        executable='yolo_detector',
        name='yolo_detector',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        yolo_node,
    ])