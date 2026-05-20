# Module : `robot_base`

**kit/** — Reusable across any ROS 2 differential-drive robot project.

## What this module does

- Describes the robot physically via URDF/Xacro (chassis, wheels, LiDAR)
- Launches Gazebo and spawns the robot model
- Broadcasts TF transforms for all robot parts
- Simulates a 360° LiDAR with realistic Gaussian noise
- Enforces velocity safety limits via `base_controller`
- Publishes robot status as JSON on `/robot_status`

## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/cmd_vel` | `geometry_msgs/Twist` | Velocity command |
| OUT | `/odom` | `nav_msgs/Odometry` | Wheel odometry |
| OUT | `/scan` | `sensor_msgs/LaserScan` | 360° LiDAR data |
| OUT | `/robot_description` | `std_msgs/String` | URDF string |
| OUT | `/robot_status` | `std_msgs/String` | JSON status |
| OUT | `/tf` | `tf2_msgs/TFMessage` | Transform tree |

## Configurable parameters (`config/robot_params.yaml`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `robot_name` | `amr_001` | Unique robot identifier |
| `max_linear_velocity` | `0.5` m/s | Forward speed limit |
| `max_angular_velocity` | `1.0` rad/s | Rotation speed limit |
| `wheel_radius` | `0.05` m | Must match URDF |
| `wheel_separation` | `0.34` m | Must match URDF |

## Standalone usage

```bash
cd ~/robotics/robotics-toolkit/projects/amr_ros2
colcon build --packages-select robot_base --symlink-install
source install/setup.bash
ros2 launch robot_base robot_base.launch.py
```

## Reuse in another project

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

robot_base = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('robot_base'), '/launch/robot_base.launch.py'
    ]),
    launch_arguments={
        'robot_name': 'my_robot',
        'x_pose': '1.0',
        'y_pose': '2.0',
    }.items()
)
```