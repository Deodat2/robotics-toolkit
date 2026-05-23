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
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('object_detector')
    params_file = os.path.join(pkg, 'config', 'detector_params.yaml')

    # Use the venv Python explicitly for YOLO
    # This ensures ultralytics and numpy<2.0 are available
    venv_python = os.path.expanduser(
        '~/robotics/robotics-toolkit/venv_vision/bin/python3'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )

    yolo_node = ExecuteProcess(
        cmd=[
            venv_python, '-m', 'object_detector.yolo_detector',
            '--ros-args',
            '--params-file', params_file,
            '-p', ['use_sim_time:=', LaunchConfiguration('use_sim_time')]
        ],
        output='screen',
    )

    return LaunchDescription([
        use_sim_time_arg,
        yolo_node,
    ])