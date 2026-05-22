"""
============================================================
FILE        : qr_navigator.launch.py
MODULE      : qr_navigator (kit/)
DESCRIPTION : Launches QR detection + waypoint manager.

DEPENDS ON:
    - robot_base.launch.py      (camera)
    - vision_bridge.launch.py   (preprocessed frames)

STANDALONE:
    ros2 launch qr_navigator qr_navigator.launch.py
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('qr_navigator')
    params_file = os.path.join(pkg, 'config', 'qr_params.yaml')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )

    # QR code detector node
    qr_detector_node = Node(
        package='qr_navigator',
        executable='qr_detector',
        name='qr_detector',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    # Waypoint manager node
    waypoint_manager_node = Node(
        package='qr_navigator',
        executable='waypoint_manager',
        name='waypoint_manager',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        qr_detector_node,
        waypoint_manager_node,
    ])