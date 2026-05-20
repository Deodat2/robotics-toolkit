"""
============================================================
FILE        : sensor_interface.launch.py
MODULE      : sensor_interface (kit/)
DESCRIPTION : Launches all sensor filter nodes.

STANDALONE:
    ros2 launch sensor_interface sensor_interface.launch.py

INCLUDED FROM PARENT LAUNCH:
    IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('sensor_interface'),
            '/launch/sensor_interface.launch.py'
        ])
    )

NOTE:
    Always launch AFTER robot_base.launch.py —
    sensors must exist before we can filter them.
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('sensor_interface')
    params_file = os.path.join(pkg, 'config', 'sensor_params.yaml')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulated clock'
    )

    # ----------------------------------------------------------
    # NODE: lidar_filter
    # Cleans raw /scan → /sensors/lidar/filtered
    # ----------------------------------------------------------
    lidar_filter_node = Node(
        package='sensor_interface',
        executable='lidar_filter',
        name='lidar_filter',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    # ----------------------------------------------------------
    # NODE: odom_filter
    # Validates /odom → /sensors/odom/filtered
    # ----------------------------------------------------------
    odom_filter_node = Node(
        package='sensor_interface',
        executable='odom_filter',
        name='odom_filter',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        lidar_filter_node,
        odom_filter_node,
    ])