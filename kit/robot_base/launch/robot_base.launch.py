"""
============================================================
FILE        : robot_base.launch.py
MODULE      : robot_base (kit/)
DESCRIPTION : Launch file — starts the complete robot_base module.

WHAT IT STARTS:
    1. Gazebo simulator (empty world)
    2. robot_state_publisher (broadcasts URDF + TF tree)
    3. Spawns the robot model in Gazebo
    4. base_controller node (safety + status)

STANDALONE USAGE:
    ros2 launch robot_base robot_base.launch.py

INCLUDED FROM ANOTHER LAUNCH FILE:
    IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            FindPackageShare('robot_base'), '/launch/robot_base.launch.py'
        ]),
        launch_arguments={'robot_name': 'amr_002'}.items()
    )

REUSABILITY:
    All arguments have sensible defaults. Override only what
    you need when including this from a parent launch file.
============================================================
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,               # Delay an action by N seconds
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    LaunchConfiguration,
    Command,                   # Run a shell command, capture output
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """
    Main entry point for the launch system.
    Returns a LaunchDescription containing all nodes and actions.
    """

    # ----------------------------------------------------------
    # PACKAGE PATHS
    # ----------------------------------------------------------
    pkg_robot_base = get_package_share_directory('robot_base')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    # Absolute paths to our config files
    urdf_file = os.path.join(pkg_robot_base, 'urdf', 'amr_robot.urdf.xacro')
    params_file = os.path.join(pkg_robot_base, 'config', 'robot_params.yaml')

    # ----------------------------------------------------------
    # LAUNCH ARGUMENTS
    # Declared here so they can be overridden from command line
    # or from a parent launch file.
    # ----------------------------------------------------------
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulated clock (true) or wall clock (false)'
    )
    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='amr_001',
        description='Unique robot name — important for multi-robot setups'
    )
    x_pose_arg = DeclareLaunchArgument(
        'x_pose', default_value='0.0',
        description='Initial X position in Gazebo world (meters)'
    )
    y_pose_arg = DeclareLaunchArgument(
        'y_pose', default_value='0.0',
        description='Initial Y position in Gazebo world (meters)'
    )

    # ----------------------------------------------------------
    # NODE 1: robot_state_publisher
    # ParameterValue(..., value_type=str) is required in ROS 2
    # Humble when passing xacro-generated URDF as a parameter.
    # Without it, ROS 2 tries to parse the URDF as YAML and fails.
    # ----------------------------------------------------------
    robot_description = ParameterValue(
        Command(['xacro ', urdf_file]),
        value_type=str        # force string type — critical fix
    )

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }]
    )

    # ----------------------------------------------------------
    # ACTION: Launch Gazebo with an empty world
    # We include Gazebo's own launch file (standard pattern)
    # ----------------------------------------------------------
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={
            'world': '',       # empty world
            'verbose': 'false',  # suppress Gazebo console spam
        }.items()
    )

    # ----------------------------------------------------------
    # NODE 2: spawn_entity
    # Sends the URDF to Gazebo to physically create the robot.
    # Delayed 3 seconds to ensure Gazebo is fully loaded first.
    # ----------------------------------------------------------
    spawn_robot = TimerAction(
        period=3.0,    # wait 3 seconds after Gazebo starts
        actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                name='spawn_robot',
                output='screen',
                arguments=[
                    '-topic', 'robot_description',
                    '-entity', LaunchConfiguration('robot_name'),
                    '-x', LaunchConfiguration('x_pose'),
                    '-y', LaunchConfiguration('y_pose'),
                    '-z', '0.1',   # slightly above ground to avoid clipping
                ],
            )
        ]
    )

    # ----------------------------------------------------------
    # NODE 3: base_controller
    # Safety layer + status publisher.
    # Also delayed to start after the robot is spawned.
    # ----------------------------------------------------------
    base_controller_node = TimerAction(
        period=5.0,
        actions=[
            Node(
                package='robot_base',
                executable='base_controller',
                name='base_controller',
                output='screen',
                parameters=[params_file],   # load robot_params.yaml
            )
        ]
    )

    # ----------------------------------------------------------
    # ASSEMBLE LAUNCH DESCRIPTION
    # Order matters: args first, then Gazebo, then nodes
    # ----------------------------------------------------------
    return LaunchDescription([
        # Arguments
        use_sim_time_arg,
        robot_name_arg,
        x_pose_arg,
        y_pose_arg,
        # Actions
        robot_state_publisher_node,
        gazebo,
        spawn_robot,
        base_controller_node,
    ])
