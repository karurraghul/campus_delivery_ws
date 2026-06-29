from launch import LaunchDescription

from launch_ros.actions import Node

from launch.substitutions import Command

from launch.substitutions import PathJoinSubstitution

from launch_ros.substitutions import FindPackageShare



def generate_launch_description():

    robot_description = Command(
        [
            "xacro ",
            PathJoinSubstitution(
                [
                    FindPackageShare("campus_robot"),
                    "urdf",
                    "campus_robot.urdf.xacro",
                ]
            ),
        ]
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "robot_description": robot_description,
            }
        ],
    )

    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        output="screen",
    )

    rviz = Node(
        package="rviz2",
        executable="rviz2",
        output="screen",
    )

    return LaunchDescription(
        [
            joint_state_publisher_gui,
            robot_state_publisher,
            rviz,
        ]
    )