from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():

    slam_params = PathJoinSubstitution([
        FindPackageShare('campus_robot'),
        'config',
        'slam_params.yaml'
    ])

    slam_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        parameters=[
            slam_params,
            {'use_sim_time': True}
        ],
        output='screen'
    )

    return LaunchDescription([slam_node])