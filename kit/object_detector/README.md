# Module : `object_detector`

**kit/** — Reusable real-time object detection for any ROS 2 robot.

## What this module does

Detects and classifies objects in real time using **YOLOv8**.
Reports object type, confidence, bounding box, and position
in the image for every frame.

Camera frame (/vision/image_preprocessed)
↓
[yolo_detector] — YOLOv8 inference
↓
/detections         → JSON list of detected objects
/detections/image   → Annotated frame with bounding boxes


## Detectable objects (COCO 80 classes)

People, bicycles, cars, trucks, boxes, bottles, chairs,
laptops, phones, and 70+ more. Or train your own model
for custom objects (your packages, robots, hazards).


## Dependencies (must run first)

robot_base.launch.py     → /camera/image_raw
vision_bridge.launch.py  → /vision/image_preprocessed


## ROS 2 Interface

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| IN | `/vision/image_preprocessed` | `sensor_msgs/Image` | Camera frames |
| OUT | `/detections` | `std_msgs/String` | JSON detections |
| OUT | `/detections/image` | `sensor_msgs/Image` | Annotated frame |
| OUT | `/detections/status` | `std_msgs/String` | JSON performance |

## Detection output format

```json
[{
  "class_id": 0,
  "class_name": "person",
  "confidence": 0.923,
  "bbox": {"x1": 120, "y1": 80, "x2": 280, "y2": 420},
  "center_x": 200,
  "center_y": 250,
  "width_px": 160,
  "height_px": 340,
  "timestamp": 1234567890.123
}]
```

## YOLO model options

| Model | Size | Speed | Accuracy | Use case |
|-------|------|-------|----------|----------|
| `yolov8n.pt` | 6MB | ⚡⚡⚡ | ★★☆ | Simulation, CPU |
| `yolov8s.pt` | 22MB | ⚡⚡☆ | ★★★ | Balanced |
| `yolov8m.pt` | 52MB | ⚡☆☆ | ★★★★ | GPU recommended |

## Custom model

```bash
# Place your trained model in models/
cp my_warehouse_model.pt kit/object_detector/models/

# Update detector_params.yaml
model_name: "my_warehouse_model.pt"
```

## Monitor performance

```bash
ros2 topic echo /detections/status
```

```json
{
  "model_loaded": true,
  "frames_processed": 450,
  "total_detections": 127,
  "avg_inference_ms": 45.2,
  "estimated_fps": 22.1,
  "current_objects": ["person", "box"]
}
```