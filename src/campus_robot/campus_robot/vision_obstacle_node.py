#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

import numpy as np
import cv2
from cv_bridge import CvBridge

import message_filters
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, PointField
from std_msgs.msg import Header


class VisionObstacleNode(Node):
    def __init__(self):
        super().__init__('vision_obstacle_node')

        # ---- Params ----
        self.declare_parameter('canny_low', 50)
        self.declare_parameter('canny_high', 150)
        self.declare_parameter('min_contour_area', 400)   # px^2, filters noise
        self.declare_parameter('max_points_per_contour', 150)
        self.declare_parameter('depth_topic', '/camera_link/depth/image_raw')
        self.declare_parameter('rgb_topic', '/camera_link/image_raw')
        self.declare_parameter('camera_info_topic', '/camera_link/depth/camera_info')
        self.declare_parameter('output_topic', '/camera/obstacles')

        self.bridge = CvBridge()
        self.fx = self.fy = self.cx = self.cy = None

        p = self.get_parameter
        rgb_topic = p('rgb_topic').value
        depth_topic = p('depth_topic').value
        info_topic = p('camera_info_topic').value

        self.info_sub = self.create_subscription(
            CameraInfo, info_topic, self.info_cb, qos_profile_sensor_data)

        rgb_sub = message_filters.Subscriber(self, Image, rgb_topic,
                                              qos_profile=qos_profile_sensor_data)
        depth_sub = message_filters.Subscriber(self, Image, depth_topic,
                                                qos_profile=qos_profile_sensor_data)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [rgb_sub, depth_sub], queue_size=5, slop=0.05)
        self.ts.registerCallback(self.image_cb)

        self.pub = self.create_publisher(
            PointCloud2, p('output_topic').value, qos_profile_sensor_data)

        self.get_logger().info('Vision obstacle node started, waiting for camera_info...')

    def info_cb(self, msg: CameraInfo):
        self.fx = msg.k[0]
        self.fy = msg.k[4]
        self.cx = msg.k[2]
        self.cy = msg.k[5]

    def image_cb(self, rgb_msg: Image, depth_msg: Image):
        if self.fx is None:
            return  # no intrinsics yet

        rgb = self.bridge.imgmsg_to_cv2(rgb_msg, desired_encoding='bgr8')
        # Gazebo depth camera publishes 32FC1 (meters)
        depth = self.bridge.imgmsg_to_cv2(depth_msg, desired_encoding='32FC1')

        gray = cv2.cvtColor(rgb, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray,
                           self.get_parameter('canny_low').value,
                           self.get_parameter('canny_high').value)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)

        min_area = self.get_parameter('min_contour_area').value
        max_pts = self.get_parameter('max_points_per_contour').value
        points = []

        for cnt in contours:
            if cv2.contourArea(cnt) < min_area:
                continue

            mask = np.zeros(depth.shape, dtype=np.uint8)
            cv2.drawContours(mask, [cnt], -1, 255, thickness=cv2.FILLED)
            ys, xs = np.where(mask == 255)
            if len(xs) == 0:
                continue

            # Subsample to keep the cloud light
            if len(xs) > max_pts:
                idx = np.random.choice(len(xs), max_pts, replace=False)
                xs, ys = xs[idx], ys[idx]

            z = depth[ys, xs]
            valid = np.isfinite(z) & (z > 0.1) & (z < 8.0)
            xs, ys, z = xs[valid], ys[valid], z[valid]
            if len(xs) == 0:
                continue

            # Pinhole projection: camera optical frame (X right, Y down, Z forward)
            x3 = (xs - self.cx) * z / self.fx
            y3 = (ys - self.cy) * z / self.fy
            pts = np.stack([x3, y3, z], axis=1)
            points.append(pts)

        if points:
            cloud_np = np.concatenate(points, axis=0).astype(np.float32)
        else:
            cloud_np = np.zeros((0, 3), dtype=np.float32)

        header = Header()
        header.stamp = depth_msg.header.stamp
        header.frame_id = depth_msg.header.frame_id  # camera optical frame
        self.pub.publish(self.make_pointcloud2(header, cloud_np))

    @staticmethod
    def make_pointcloud2(header, points_xyz):
        fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = points_xyz.shape[0]
        msg.fields = fields
        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = msg.point_step * msg.width
        msg.is_dense = True
        msg.data = points_xyz.tobytes()
        return msg


def main(args=None):
    rclpy.init(args=args)
    node = VisionObstacleNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
