"""
============================================================
FILE        : nav2_config.launch.py
MODULE      : nav2_config (kit/)
DESCRIPTION : Launches the complete Nav2 navigation stack.

WHAT IT STARTS:
    1. Nav2 bringup (AMCL + planner + controller + BT navigator)
    2. mission_client node (clean goal-sending API)

DEPENDS ON (must be running first):
    - robot_base.launch.py
    - sensor_interface.launch.py
    - slam_module.launch.py   (for /map topic)

STANDALONE TEST:
    # Terminal 1: ros2 launch robot_base robot_base.launch.py
    # Terminal 2: ros2 launch sensor_interface sensor_interface.launch.py
    # Terminal 3: ros2 launch slam_module slam_module.launch.py
    # Terminal 4: ros2 launch nav2_config nav2_config.launch.py

REUSABILITY:
    Override nav2_params_file to use a different config.
    Override map_yaml_file to navigate on a pre-built map.
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_nav2_config = get_package_share_directory('nav2_config')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    nav2_params_file = os.path.join(
        pkg_nav2_config, 'config', 'nav2_params.yaml'
    )

    # ----------------------------------------------------------
    # ARGUMENTS
    # ----------------------------------------------------------
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )
    map_yaml_arg = DeclareLaunchArgument(
        'map_yaml_file', default_value='',
        description='Path to saved map .yaml (empty = use live SLAM map)'
    )

    # ----------------------------------------------------------
    # Nav2 bringup
    # Includes all Nav2 nodes: AMCL, planner, controller, BT
    # We use the official nav2_bringup launch as base
    # ----------------------------------------------------------
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'navigation_launch.py')
        ),
        launch_arguments={
            'use_sim_time':  LaunchConfiguration('use_sim_time'),
            'params_file':   nav2_params_file,
            'autostart':     'true',
        }.items()
    )

    # ----------------------------------------------------------
    # mission_client node
    # Clean API for sending navigation goals
    # Delayed 5s to ensure Nav2 is fully started
    # ----------------------------------------------------------
    mission_client_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='nav2_config',
                executable='mission_client',
                name='mission_client',
                output='screen',
                parameters=[{
                    'use_sim_time': LaunchConfiguration('use_sim_time'),
                }]
            )
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        map_yaml_arg,
        nav2_bringup,
        mission_client_node,
    ])