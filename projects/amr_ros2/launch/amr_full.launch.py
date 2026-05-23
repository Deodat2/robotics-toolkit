"""
============================================================
FILE        : amr_full.launch.py
PROJECT     : amr_ros2
DESCRIPTION : Master launch file — starts the complete AMR system.

LAUNCHES IN ORDER:
    1. Gazebo + warehouse world
    2. robot_base     (robot + LiDAR + camera)
    3. sensor_interface (filter LiDAR/odom)
    4. slam_module    (real-time mapping)
    5. nav2_config    (autonomous navigation)
    6. vision_bridge  (camera preprocessing)
    7. qr_navigator   (QR detection + waypoints)
    8. object_detector (YOLO detection)
    9. fleet_manager  (mission orchestration)
    10. collision_manager (inter-robot safety)

USAGE:
    ros2 launch amr_ros2_bringup amr_full.launch.py
    ros2 launch amr_ros2_bringup amr_full.launch.py vision:=false
    ros2 launch amr_ros2_bringup amr_full.launch.py fleet:=false
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
    GroupAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # ----------------------------------------------------------
    # PATHS
    # ----------------------------------------------------------
    amr_launch_dir = os.path.dirname(os.path.abspath(__file__))
    warehouse_world = os.path.join(
        amr_launch_dir, '..', 'worlds', 'warehouse.world'
    )

    # ----------------------------------------------------------
    # ARGUMENTS — enable/disable subsystems
    # ----------------------------------------------------------
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use Gazebo simulated clock'
    )
    vision_arg = DeclareLaunchArgument(
        'vision', default_value='true',
        description='Launch vision AI modules (vision_bridge, qr, yolo)'
    )
    fleet_arg = DeclareLaunchArgument(
        'fleet', default_value='true',
        description='Launch fleet and collision manager'
    )
    slam_arg = DeclareLaunchArgument(
        'slam', default_value='true',
        description='Launch SLAM module'
    )
    nav_arg = DeclareLaunchArgument(
        'nav', default_value='true',
        description='Launch Nav2 navigation stack'
    )

    # ----------------------------------------------------------
    # 1. robot_base (Gazebo + robot + sensors)
    # No delay — first to start
    # ----------------------------------------------------------
    robot_base = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('robot_base'),
            '/launch/robot_base.launch.py'
        ]),
        launch_arguments={
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }.items()
    )

    # ----------------------------------------------------------
    # 2. sensor_interface — delay 5s (wait for Gazebo + robot)
    # ----------------------------------------------------------
    sensor_interface = TimerAction(
        period=5.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('sensor_interface'),
                '/launch/sensor_interface.launch.py'
            ]),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items()
        )]
    )

    # ----------------------------------------------------------
    # 3. slam_module — delay 8s (wait for sensors)
    # ----------------------------------------------------------
    slam_module = TimerAction(
        period=8.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('slam_module'),
                '/launch/slam_module.launch.py'
            ]),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
            condition=IfCondition(LaunchConfiguration('slam'))
        )]
    )

    # ----------------------------------------------------------
    # 4. nav2_config — delay 12s (wait for SLAM map)
    # ----------------------------------------------------------
    nav2 = TimerAction(
        period=12.0,
        actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                FindPackageShare('nav2_config'),
                '/launch/nav2_config.launch.py'
            ]),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
            condition=IfCondition(LaunchConfiguration('nav'))
        )]
    )

    # ----------------------------------------------------------
    # 5. vision modules — delay 10s (wait for camera)
    # ----------------------------------------------------------
    vision_modules = TimerAction(
        period=10.0,
        actions=[GroupAction(
            condition=IfCondition(LaunchConfiguration('vision')),
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        FindPackageShare('vision_bridge'),
                        '/launch/vision_bridge.launch.py'
                    ]),
                    launch_arguments={
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                    }.items()
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        FindPackageShare('qr_navigator'),
                        '/launch/qr_navigator.launch.py'
                    ]),
                    launch_arguments={
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                    }.items()
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        FindPackageShare('object_detector'),
                        '/launch/object_detector.launch.py'
                    ]),
                    launch_arguments={
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                    }.items()
                ),
            ]
        )]
    )

    # ----------------------------------------------------------
    # 6. fleet modules — delay 15s (wait for nav2)
    # ----------------------------------------------------------
    fleet_modules = TimerAction(
        period=15.0,
        actions=[GroupAction(
            condition=IfCondition(LaunchConfiguration('fleet')),
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        FindPackageShare('fleet_manager'),
                        '/launch/fleet_manager.launch.py'
                    ]),
                    launch_arguments={
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                    }.items()
                ),
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource([
                        FindPackageShare('collision_manager'),
                        '/launch/collision_manager.launch.py'
                    ]),
                    launch_arguments={
                        'use_sim_time': LaunchConfiguration('use_sim_time'),
                    }.items()
                ),
            ]
        )]
    )

    return LaunchDescription([
        # Arguments
        use_sim_time_arg,
        vision_arg,
        fleet_arg,
        slam_arg,
        nav_arg,
        # Modules (in order)
        robot_base,
        sensor_interface,
        slam_module,
        nav2,
        vision_modules,
        fleet_modules,
    ])