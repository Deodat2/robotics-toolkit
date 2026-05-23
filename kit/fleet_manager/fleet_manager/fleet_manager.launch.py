"""
============================================================
FILE        : fleet_manager.launch.py
MODULE      : fleet_manager (kit/)
DESCRIPTION : Launches the fleet orchestration node.

STANDALONE:
    ros2 launch fleet_manager fleet_manager.launch.py
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('fleet_manager')
    params_file = os.path.join(pkg, 'config', 'fleet_params.yaml')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )

    orchestrator_node = Node(
        package='fleet_manager',
        executable='fleet_orchestrator',
        name='fleet_orchestrator',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        orchestrator_node,
    ])
