from launch import LaunchDescription

from launch.actions import IncludeLaunchDescription

from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch.substitutions import Command

from launch.substitutions import PathJoinSubstitution

from launch_ros.actions import Node

from launch_ros.substitutions import FindPackageShare



def generate_launch_description():

    pkg_share = FindPackageShare("campus_robot")

    world = PathJoinSubstitution(
        [
            pkg_share,
            "worlds",
            "campus_v2.world",
        ]
    )

    robot_description = Command(
        [
            "xacro ",
            PathJoinSubstitution(
                [
                    pkg_share,
                    "urdf",
                    "campus_robot.urdf.xacro",
                ]
            ),
        ]
    )

    gazebo = IncludeLaunchDescription(

        PythonLaunchDescriptionSource(

            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("gazebo_ros"),
                        "launch",
                        "gazebo.launch.py",
                    ]
                )
            ]
        ),

        launch_arguments={
            "world": world,
        }.items(),

    )

    robot_state_publisher = Node(

        package="robot_state_publisher",

        executable="robot_state_publisher",

        parameters=[
            {
                "robot_description": robot_description,
                "use_sim_time": True,
            }
        ],

        output="screen",

    )

    spawn_robot = Node(

        package="gazebo_ros",

        executable="spawn_entity.py",

        arguments=[
            "-topic",
            "robot_description",

            "-entity",
            "campus_robot",

            "-x",
            "0",

            "-y",
            "0",

            "-z",
            "0.10",
        ],

        output="screen",

    )

    return LaunchDescription(

        [

            gazebo,

            robot_state_publisher,

            spawn_robot,

        ]

    )