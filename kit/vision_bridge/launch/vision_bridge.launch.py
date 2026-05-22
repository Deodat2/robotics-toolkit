"""
============================================================
FILE        : vision_bridge.launch.py
MODULE      : vision_bridge (kit/)
DESCRIPTION : Launches camera preprocessing node.

DEPENDS ON:
    - robot_base.launch.py (provides /camera/image_raw)

STANDALONE:
    ros2 launch vision_bridge vision_bridge.launch.py
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg = get_package_share_directory('vision_bridge')
    params_file = os.path.join(pkg, 'config', 'vision_params.yaml')

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo clock'
    )

    camera_node = Node(
        package='vision_bridge',
        executable='camera_node',
        name='camera_node',
        output='screen',
        parameters=[
            params_file,
            {'use_sim_time': LaunchConfiguration('use_sim_time')}
        ]
    )

    return LaunchDescription([
        use_sim_time_arg,
        camera_node,
    ])