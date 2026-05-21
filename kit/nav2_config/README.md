# Module : `nav2_config` 🧭

**kit/** — Reusable across any ROS 2 differential-drive robot project.

## What this module does

Provides a fully configured **Nav2 navigation stack** for autonomous
point-to-point navigation. Tell the robot where to go — it figures
out the path, follows it, and avoids obstacles along the way.

You say    : "Go to (3.0, 2.0)"
Nav2 does  : localize → plan path → follow path → avoid obstacles
Robot does : moves autonomously, stops when arrived


## Navigation stack components

| Component | Role |
|-----------|------|
| **AMCL** | Localizes robot on the map using particles |
| **Planner (NavFn/A*)** | Computes optimal global path to goal |
| **Controller (DWB)** | Follows path, avoids dynamic obstacles |
| **Behavior Server** | Recovery when robot gets stuck (spin, backup, wait) |
| **BT Navigator** | Orchestrates all components via behavior tree |
| **MissionClient** | Clean Python API to send goals |

## Dependencies (must run first)

robot_base.launch.py         → /tf, /odom, base_footprint
sensor_interface.launch.py   → /sensors/lidar/filtered, /sensors/odom/filtered
slam_module.launch.py        → /map (live SLAM or saved map)


## ROS 2 Interface

| Direction | Topic / Action | Type | Description |
|-----------|---------------|------|-------------|
| IN | `/map` | `nav_msgs/OccupancyGrid` | Map from SLAM |
| IN | `/sensors/lidar/filtered` | `sensor_msgs/LaserScan` | Obstacle detection |
| IN | `/sensors/odom/filtered` | `nav_msgs/Odometry` | Robot position |
| OUT | `/cmd_vel` | `geometry_msgs/Twist` | Wheel commands |
| OUT | `/nav/status` | `std_msgs/String` | JSON navigation status |
| ACTION | `/navigate_to_pose` | `nav2_msgs/NavigateToPose` | Goal sending |

## Key parameters (`config/nav2_params.yaml`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `robot_radius` | `0.22` m | Robot physical size — critical for safety |
| `max_vel_x` | `0.5` m/s | Max forward speed |
| `xy_goal_tolerance` | `0.25` m | Arrival precision |
| `inflation_radius` | `0.55` m | Safety margin around walls |
| `use_astar` | `true` | A* (fast) vs Dijkstra (safer) |

## Standalone usage

```bash
# Terminal 1
ros2 launch robot_base robot_base.launch.py

# Terminal 2
ros2 launch sensor_interface sensor_interface.launch.py

# Terminal 3
ros2 launch slam_module slam_module.launch.py

# Terminal 4
cd ~/robotics/robotics-toolkit/projects/amr_ros2
colcon build --packages-select nav2_config --symlink-install
source install/setup.bash
ros2 launch nav2_config nav2_config.launch.py
```

## Send a navigation goal

### Via command line
```bash
ros2 topic pub /goal_pose geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: 'map'}, pose: {position: {x: 2.0, y: 1.0}}}" \
  --once
```

### Via RViz2 (easiest)
1. Open RViz2 with the 4 modules running
2. Click **"2D Goal Pose"** in the toolbar
3. Click anywhere on the map → robot navigates there

### Via Python (MissionClient API)
```python
from nav2_config.mission_client import MissionClient
import rclpy

rclpy.init()
client = MissionClient()

# Send goal — non-blocking
client.go_to(x=3.0, y=2.0, yaw=0.0)

rclpy.spin(client)
```

## Monitor navigation status

```bash
ros2 topic echo /nav/status
```

Output example:
```json
{
  "robot_name": "amr_001",
  "nav_status": "navigating",
  "goal_x": 3.0,
  "goal_y": 2.0,
  "goals_completed": 2,
  "goals_failed": 0
}
```

## Tuning for different robots

```yaml
# Small fast robot (e.g. TurtleBot)
robot_radius:     0.15
max_vel_x:        0.8
inflation_radius: 0.35

# Large slow robot (e.g. warehouse AMR)
robot_radius:     0.35
max_vel_x:        0.3
inflation_radius: 0.7
```

## Reuse in another project

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

nav2 = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('nav2_config'),
        '/launch/nav2_config.launch.py'
    ]),
    launch_arguments={
        'use_sim_time': 'true',
        # Optional: navigate on a pre-built map
        # 'map_yaml_file': '/path/to/your/map.yaml',
    }.items()
)
```