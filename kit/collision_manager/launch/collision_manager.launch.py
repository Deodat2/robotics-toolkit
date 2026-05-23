"""
============================================================
FILE        : collision_manager.launch.py
MODULE      : collision_manager (kit/)
DESCRIPTION : Launches collision prevention node.

DEPENDS ON:
    - fleet_manager.launch.py (provides /fleet/status)

STANDALONE:
    ros2 launch collision_manager collision_manager.launch.py
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('collision_manager')
    params_file = os.path.join(pkg, 'config', 'collision_params.yaml')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )

    monitor_node = Node(
        package='collision_manager',
        executable='collision_monitor',
        name='collision_monitor',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        monitor_node,
    ])