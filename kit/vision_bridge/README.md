# Module : `vision_bridge`

**kit/** — Reusable foundation for all vision modules in any ROS 2 project.

## What this module does

Acts as the **bridge between ROS 2 image topics and OpenCV**.
All vision modules (`qr_navigator`, `object_detector`) build on top
of this module — they never deal with cv_bridge directly.

Gazebo / Real Camera
↓
/camera/image_raw  (sensor_msgs/Image)
↓
[vision_bridge]
├── ImageConverter  → ROS 2 Image ↔ OpenCV numpy array
└── CameraNode      → preprocesses + republishes frames
↓
/vision/image_preprocessed  (clean frames for vision modules)


## Components

| File | Role |
|------|------|
| `image_converter.py` | Utility class: ROS 2 ↔ OpenCV conversion |
| `camera_node.py` | ROS 2 node: subscribes, preprocesses, republishes |

## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/camera/image_raw` | `sensor_msgs/Image` | Raw camera frames |
| OUT | `/vision/image_preprocessed` | `sensor_msgs/Image` | Clean resized frames |
| OUT | `/vision/camera_status` | `std_msgs/String` | JSON health status |

## Configurable parameters (`config/vision_params.yaml`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `input_topic` | `/camera/image_raw` | Source camera topic |
| `output_width` | `640` | Output frame width (px) |
| `output_height` | `480` | Output frame height (px) |
| `publish_debug` | `true` | Publish annotated debug frames |
| `status_rate` | `1.0` Hz | Camera status publish rate |

## Monitor camera health

```bash
ros2 topic echo /vision/camera_status
```

Output example:
```json
{
  "frames_received": 1247,
  "frames_failed": 0,
  "last_shape": "(480, 640, 3)",
  "output_size": "640x480"
}
```

## Standalone usage

```bash
# Terminal 1 — robot with camera
ros2 launch robot_base robot_base.launch.py

# Terminal 2 — vision bridge
cd ~/robotics/robotics-toolkit/projects/amr_ros2
colcon build --packages-select vision_bridge --symlink-install
source install/setup.bash
ros2 launch vision_bridge vision_bridge.launch.py
```

## Reuse in another project — ImageConverter API

```python
# In your vision module node
from vision_bridge.image_converter import ImageConverter
import cv2
import numpy as np

class MyVisionNode(Node):
    def __init__(self):
        super().__init__('my_vision_node')

        # Subscribe to camera — receive frames as numpy arrays
        self.converter = ImageConverter(
            node=self,
            image_topic='/vision/image_preprocessed',
            callback=self._on_frame,
            encoding='bgr8'
        )

    def _on_frame(self, frame: np.ndarray):
        # frame is a BGR numpy array — standard OpenCV format
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # ... your vision processing here
```

## Static conversion utilities

```python
# One-shot ROS 2 Image → numpy (no subscription needed)
frame = ImageConverter.ros_to_cv2(ros_image_msg, encoding='bgr8')

# numpy → ROS 2 Image (to publish processed result)
ros_msg = ImageConverter.cv2_to_ros(frame, encoding='bgr8')
```

## Reuse in another project — launch file

```python
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

vision_bridge = IncludeLaunchDescription(
    PythonLaunchDescriptionSource([
        FindPackageShare('vision_bridge'),
        '/launch/vision_bridge.launch.py'
    ]),
    launch_arguments={
        # Override for a different camera topic
        'use_sim_time': 'true',
    }.items()
)
```

## Compatibility

| Component | Version |
|-----------|---------|
| ROS 2 | Humble |
| OpenCV | 4.5.4+ (system) |
| cv_bridge | 3.2.1+ |
| Python | 3.10 |
| venv | `venv_vision` with `--system-site-packages` |