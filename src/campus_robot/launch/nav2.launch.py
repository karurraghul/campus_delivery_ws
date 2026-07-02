from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    pkg_share = FindPackageShare("campus_robot")

    default_map = PathJoinSubstitution([pkg_share, "maps", "campus_map.yaml"])
    default_params = PathJoinSubstitution([pkg_share, "config", "nav2_params.yaml"])
    default_rviz_config = PathJoinSubstitution(
        [pkg_share, "rviz", "campus_robot.rviz"])

    map_yaml_file = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    use_rviz = LaunchConfiguration("use_rviz")
    rviz_config_file = LaunchConfiguration("rviz_config")

    declare_map_cmd = DeclareLaunchArgument(
        "map",
        default_value=default_map,
        description="Full path to the map yaml file to load",
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        "params_file",
        default_value=default_params,
        description="Full path to the Nav2 parameters file to use",
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="True",
        description="Use simulation (Gazebo) clock if true",
    )

    declare_autostart_cmd = DeclareLaunchArgument(
        "autostart",
        default_value="True",
        description="Automatically startup the Nav2 stack",
    )

    declare_use_rviz_cmd = DeclareLaunchArgument(
        "use_rviz",
        default_value="True",
        description="Whether to start RViz alongside Nav2",
    )

    declare_rviz_config_cmd = DeclareLaunchArgument(
        "rviz_config",
        default_value=default_rviz_config,
        description="Full path to the RViz config file to use",
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [
                        FindPackageShare("nav2_bringup"),
                        "launch",
                        "bringup_launch.py",
                    ]
                )
            ]
        ),
        launch_arguments={
            "map": map_yaml_file,
            "params_file": params_file,
            "use_sim_time": use_sim_time,
            "autostart": autostart,
            "slam": "False",
        }.items(),
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        arguments=["-d", rviz_config_file],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription(
        [
            declare_map_cmd,
            declare_params_file_cmd,
            declare_use_sim_time_cmd,
            declare_autostart_cmd,
            declare_use_rviz_cmd,
            declare_rviz_config_cmd,
            nav2_bringup,
            rviz_node,
        ]
    )
