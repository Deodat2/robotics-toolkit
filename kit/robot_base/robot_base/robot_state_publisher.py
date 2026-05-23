"""
============================================================
FILE        : robot_state_publisher.py
MODULE      : robot_base (kit/)
DESCRIPTION : Wrapper node around ROS 2 robot_state_publisher.

WHAT IT DOES:
    Reads the URDF file, then continuously broadcasts the
    position (TF transform) of every robot part relative
    to each other. Every other module (SLAM, Nav2, RViz)
    depends on these transforms to know where things are.

TOPICS PUBLISHED:
    /robot_description  (std_msgs/String)     — raw URDF string
    /tf                 (tf2_msgs/TFMessage)  — transforms tree
    /tf_static          (tf2_msgs/TFMessage)  — static transforms

REUSABILITY:
    Pass a different URDF path via the 'urdf_path' parameter
    to use this node with any robot description file.
============================================================
"""

import os
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class RobotDescriptionPublisher(Node):
    """
    Loads the URDF file and publishes it on /robot_description.

    The standard robot_state_publisher node will pick this up
    and handle all TF broadcasting automatically.
    """

    def __init__(self):
        super().__init__('robot_description_publisher')

        # --------------------------------------------------
        # PARAMETER: path to the URDF/xacro file
        # Declared as a ROS 2 parameter so it can be
        # overridden from a launch file or command line.
        # --------------------------------------------------
        self.declare_parameter(
            'urdf_path',
            ''  # empty default — must be set at launch
        )

        urdf_path = self.get_parameter('urdf_path').value

        # Validate the path exists before trying to read it
        if not urdf_path or not os.path.exists(urdf_path):
            self.get_logger().error(
                f'URDF file not found: "{urdf_path}". '
                f'Set the urdf_path parameter in your launch file.'
            )
            return

        # --------------------------------------------------
        # Read the URDF file content
        # --------------------------------------------------
        with open(urdf_path, 'r') as f:
            urdf_content = f.read()

        # --------------------------------------------------
        # Publisher: /robot_description
        # QoS "latching" behavior: new subscribers immediately
        # receive the last published message (important because
        # some nodes subscribe after this node starts).
        # --------------------------------------------------
        from rclpy.qos import QoSProfile, DurabilityPolicy
        qos = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL  # "latching"
        )

        self._publisher = self.create_publisher(
            String, 'robot_description', qos)

        # Publish once — the QoS latching keeps it available
        msg = String()
        msg.data = urdf_content
        self._publisher.publish(msg)

        self.get_logger().info(
            f'Robot description published from: {urdf_path}'
        )


def main(args=None):
    """Entry point — called by: ros2 run robot_base robot_state_publisher"""
    rclpy.init(args=args)
    node = RobotDescriptionPublisher()
    rclpy.spin(node)       # Keep node alive, processing callbacks
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
