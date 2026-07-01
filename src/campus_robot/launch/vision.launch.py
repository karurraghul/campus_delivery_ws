from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    vision_obstacle_node = Node(
        package="campus_robot",
        executable="vision_obstacle_node",
        name="vision_obstacle_node",
        output="screen",
        parameters=[{"use_sim_time": True}],
    )

    return LaunchDescription(
        [
            vision_obstacle_node,
        ]
    )
