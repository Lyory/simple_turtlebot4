"""Open Gazebo and RViz for mapping, localization or Nav2 navigation."""
from pathlib import Path
from shlex import quote

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
    SetEnvironmentVariable, TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description():
    root = Path(__file__).resolve().parents[1]
    bringup = Path(get_package_share_directory('turtlebot4_ignition_bringup'))
    navigation = Path(get_package_share_directory('turtlebot4_navigation'))
    gazebo_args = (
        f'{quote(str(root / "worlds" / "maze_fast.sdf"))} -r -v 4 '
        '--render-engine-server ogre2 --render-engine-gui ogre2 '
        f'--gui-config {quote(str(bringup / "gui" / "standard" / "gui.config"))}'
    )
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='mapping',
                              choices=['mapping', 'localization', 'navigation']),
        DeclareLaunchArgument('map', default_value=str(root / 'maps' / 'map.yaml')),
        SetEnvironmentVariable('LIBGL_ALWAYS_SOFTWARE', '0'),
        SetEnvironmentVariable('__GLX_VENDOR_LIBRARY_NAME', 'nvidia'),
        SetEnvironmentVariable('__NV_PRIME_RENDER_OFFLOAD', '1'),
        # Override the stock Create 3 OGRE1 sensor engine. OGRE1 caps GPU
        # lidar at 180 degrees; RPLIDAR is configured for a full 360-degree scan.
        GroupAction([
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(bringup / 'launch' / 'ignition.launch.py')),
                launch_arguments={'world': str(root / 'worlds' / 'maze_fast'),
                                  'model': 'standard',
                                  'gz_args': gazebo_args}.items())]),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(bringup / 'launch' / 'turtlebot4_spawn.launch.py')),
            launch_arguments={'model': 'standard', 'rviz': 'false',
                              'use_sim_time': 'true', 'x': '0.0', 'y': '0.0',
                              'yaw': '3.141592653589793',
                              'world': 'maze', 'slam': 'false',
                              'nav2': 'false', 'localization': 'false'}.items()),
        # Ignore scans during spawning while the robot settles on the floor.
        TimerAction(period=15.0, actions=[
            Node(package='slam_toolbox', executable='async_slam_toolbox_node',
                 name='slam_toolbox',
                 parameters=[str(root / 'config' / 'slam.yaml'),
                             {'use_sim_time': True}], output='screen',
                 condition=IfCondition(PythonExpression([
                     "'", LaunchConfiguration('mode'), "' == 'mapping'",
                 ]))),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(navigation / 'launch' / 'localization.launch.py')),
                launch_arguments={'map': LaunchConfiguration('map'),
                                  'use_sim_time': 'true'}.items(),
                condition=IfCondition(PythonExpression([
                    "'", LaunchConfiguration('mode'), "' in ['localization', 'navigation']",
                ]))),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(str(navigation / 'launch' / 'nav2.launch.py')),
                launch_arguments={'use_sim_time': 'true',
                                  'params_file': str(root / 'config' / 'nav2.yaml')}.items(),
                condition=IfCondition(PythonExpression([
                    "'", LaunchConfiguration('mode'), "' == 'navigation'",
                ]))),
        ]),
        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', str(root / 'config' / 'simulation.rviz')],
             parameters=[{'use_sim_time': True}], output='screen'),
    ])
