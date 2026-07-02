from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    pkg_share = FindPackageShare("campus_robot")
    default_waypoints_file = PathJoinSubstitution(
        [pkg_share, "config", "waypoints_v2.yaml"])

    waypoints_file = LaunchConfiguration("waypoints_file")
    route = LaunchConfiguration("route")
    return_to_gate = LaunchConfiguration("return_to_gate")
    use_sim_time = LaunchConfiguration("use_sim_time")

    declare_waypoints_file_cmd = DeclareLaunchArgument(
        "waypoints_file",
        default_value=default_waypoints_file,
        description="Full path to the waypoints yaml file",
    )

    declare_route_cmd = DeclareLaunchArgument(
        "route",
        default_value="library,admin_block,canteen,hostel,medical_center",
        description="Comma-separated ordered list of waypoint names to visit",
    )

    declare_return_to_gate_cmd = DeclareLaunchArgument(
        "return_to_gate",
        default_value="True",
        description="Whether to return to main_gate after the last stop",
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        "use_sim_time",
        default_value="True",
        description="Use simulation (Gazebo) clock if true",
    )

    waypoint_nav_node = Node(
        package="campus_robot",
        executable="waypoint_nav_node",
        name="waypoint_nav_node",
        output="screen",
        parameters=[{
            "waypoints_file": waypoints_file,
            "route": route,
            "return_to_gate": return_to_gate,
            "use_sim_time": use_sim_time,
        }],
    )

    return LaunchDescription(
        [
            declare_waypoints_file_cmd,
            declare_route_cmd,
            declare_return_to_gate_cmd,
            declare_use_sim_time_cmd,
            waypoint_nav_node,
        ]
    )
