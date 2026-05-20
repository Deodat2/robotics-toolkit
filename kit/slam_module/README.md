# Module : `slam_module` 🗺️

**kit/** — Reusable across any ROS 2 robot with a 2D LiDAR.

## What this module does

Builds a 2D map of the environment in real time while
simultaneously tracking the robot's position on that map.
Uses **slam_toolbox** (industry standard, used in production robots).

Robot moves → LiDAR scans → slam_toolbox matches scans
→ builds OccupancyGrid map → estimates robot pose on map
→ map grows as robot explores → save map when done


## Dependencies (must run first)

robot_base.launch.py        → provides /tf, /odom, base_footprint
sensor_interface.launch.py  → provides /sensors/lidar/filtered


## ROS 2 Interface

| Direction | Topic / Service | Type | Description |
|-----------|----------------|------|-------------|
| IN | `/sensors/lidar/filtered` | `sensor_msgs/LaserScan` | Clean LiDAR data |
| IN | `/odom` | `nav_msgs/Odometry` | Wheel odometry |
| IN | `/tf` | `tf2_msgs/TFMessage` | Robot transforms |
| OUT | `/map` | `nav_msgs/OccupancyGrid` | Live 2D map |
| OUT | `/slam/status` | `std_msgs/String` | JSON exploration stats |
| SRV | `/slam/save_map` | `std_srvs/Trigger` | Save map to disk |

## Map values (OccupancyGrid)

| Value | Meaning |
|-------|---------|
| `-1` | Unknown — not yet explored |
| `0` | Free space — robot can drive here |
| `100` | Occupied — wall or obstacle |

## Configurable parameters (`config/slam_params.yaml`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `mode` | `mapping` | `mapping` or `localization` |
| `resolution` | `0.05` m | Map precision (5 cm/pixel) |
| `map_update_interval` | `2.0` s | How often map updates |
| `minimum_travel_distance` | `0.2` m | Min move before update |
| `do_loop_closing` | `true` | Correct drift when revisiting |
| `max_laser_range` | `10.0` m | Must match LiDAR config |
| `scan_topic` | `/sensors/lidar/filtered` | Input LiDAR topic |

## Environment presets

```yaml
# Warehouse (default) — large open space
resolution: 0.05
loop_search_maximum_distance: 3.0
max_laser_range: 10.0

# Office — small rooms, narrow doors
resolution: 0.03
loop_search_maximum_distance: 1.5
max_laser_range: 8.0
```

## Standalone usage

```bash
# Terminal 1
ros2 launch robot_base robot_base.launch.py

# Terminal 2
ros2 launch sensor_interface sensor_interface.launch.py

# Terminal 3
cd ~/robotics/robotics-toolkit/projects/amr_ros2
colcon build --packages-select slam_module --symlink-install
source install/setup.bash
ros2 launch slam_module slam_module.launch.py
```

## Save the map when exploration is done

```bash
ros2 service call /slam/save_map std_srvs/srv/Trigger
```

Generates two files in `maps/`:
- `warehouse_map.pgm` — grayscale image of the map
- `warehouse_map.yaml` — map metadata (resolution, origin)

## Monitor exploration progress

```bash
ros2 topic echo /slam/status
```

Output example:
```json
{
  "map_received": true,
  "map_width": 384,
  "map_height": 384,
  "resolution_m": 0.05,
  "explored_pct": 34.2,
  "explored_cells": 50431,
  "total_cells": 147456
}
```

## Reuse in another project

```python
# In your parent launch file
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

slam = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('slam_module'), '/launch/slam_module.launch.py'
    ]),
    # Override scan topic if your robot uses a different one
    launch_arguments={
        'use_sim_time': 'true',
    }.items()
)
```