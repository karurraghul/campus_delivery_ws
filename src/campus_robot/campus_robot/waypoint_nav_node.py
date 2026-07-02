#!/usr/bin/env python3
"""Autonomous campus delivery route runner.

Reads waypoints_v2.yaml, sets AMCL's initial pose to the `main_gate` entry
(which must match the robot's Gazebo spawn pose in gazebo.launch.py), waits
for Nav2 to become active, then drives the robot through an ordered list of
building waypoints using Nav2's FollowWaypoints action.
"""
import math

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def yaw_to_quaternion(yaw):
    return (0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0))


def make_pose(navigator, x, y, yaw, frame_id='map'):
    pose = PoseStamped()
    pose.header.frame_id = frame_id
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = 0.0
    qx, qy, qz, qw = yaw_to_quaternion(float(yaw))
    pose.pose.orientation.x = qx
    pose.pose.orientation.y = qy
    pose.pose.orientation.z = qz
    pose.pose.orientation.w = qw
    return pose


def load_waypoints(path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return data['waypoints']


def main():
    rclpy.init()

    navigator = BasicNavigator()

    default_waypoints_file = get_package_share_directory('campus_robot') + \
        '/config/waypoints_v2.yaml'
    navigator.declare_parameter('waypoints_file', default_waypoints_file)
    navigator.declare_parameter(
        'route', 'library,admin_block,canteen,hostel,medical_center')
    navigator.declare_parameter('return_to_gate', True)

    waypoints_file = navigator.get_parameter(
        'waypoints_file').get_parameter_value().string_value
    route_param = navigator.get_parameter(
        'route').get_parameter_value().string_value
    return_to_gate = navigator.get_parameter(
        'return_to_gate').get_parameter_value().bool_value

    waypoints = load_waypoints(waypoints_file)

    if 'main_gate' not in waypoints:
        navigator.error(
            "waypoints file '%s' has no 'main_gate' entry — cannot set "
            "initial pose" % waypoints_file)
        rclpy.shutdown()
        return

    gate = waypoints['main_gate']
    initial_pose = make_pose(navigator, gate['x'], gate['y'], gate['yaw'])

    navigator.info(
        'Setting AMCL initial pose to spawn/main_gate: '
        'x=%.2f y=%.2f yaw=%.4f' % (gate['x'], gate['y'], gate['yaw']))
    navigator.setInitialPose(initial_pose)

    navigator.waitUntilNav2Active()

    route_names = [name.strip() for name in route_param.split(',') if name.strip()]
    unknown = [name for name in route_names if name not in waypoints]
    if unknown:
        navigator.error(
            'Unknown waypoint name(s) in route: %s. Available: %s' %
            (unknown, list(waypoints.keys())))
        rclpy.shutdown()
        return

    goal_poses = []
    for name in route_names:
        wp = waypoints[name]
        navigator.info(
            'Route stop: %s (%.2f, %.2f) — %s' %
            (name, wp['x'], wp['y'], wp.get('description', '')))
        goal_poses.append(make_pose(navigator, wp['x'], wp['y'], wp['yaw']))

    if return_to_gate:
        navigator.info('Route will return to main_gate after final stop.')
        goal_poses.append(initial_pose)
        route_names = route_names + ['main_gate']

    navigator.followWaypoints(goal_poses)

    last_reported = -1
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback and feedback.current_waypoint != last_reported:
            last_reported = feedback.current_waypoint
            if last_reported < len(route_names):
                navigator.info(
                    'Heading to waypoint %d/%d: %s' %
                    (last_reported + 1, len(route_names),
                     route_names[last_reported]))

    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.info('Delivery route complete — all waypoints reached.')
    elif result == TaskResult.CANCELED:
        navigator.warn('Delivery route was canceled.')
    elif result == TaskResult.FAILED:
        navigator.error('Delivery route failed.')
    else:
        navigator.info('Delivery route finished with unknown result.')

    navigator.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
