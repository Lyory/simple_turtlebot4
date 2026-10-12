# TurtleBot 4 — Ubuntu 22.04 / ROS 2 Humble

Yêu cầu: đã cài ROS 2 Humble và driver NVIDIA (launch hiện dùng NVIDIA).

## 1. Cài đặt và build

```bash
sudo apt update
sudo apt install git python3-colcon-common-extensions python3-rosdep \
  ros-humble-turtlebot4-simulator ros-humble-turtlebot4-desktop \
  ros-humble-irobot-create-nodes ros-humble-navigation2 \
  ros-humble-slam-toolbox ros-humble-teleop-twist-keyboard

git clone https://github.com/Lyory/simple_turtlebot4.git ~/simple_turtlebot4
cd ~/simple_turtlebot4
source /opt/ros/humble/setup.bash
sudo rosdep init  # Chỉ chạy nếu rosdep chưa được khởi tạo
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
```

Dependency simulator: [TurtleBot 4 Humble](https://turtlebot.github.io/turtlebot4-user-manual/software/turtlebot4_simulator.html).

Trong **mỗi terminal mới**, chạy trước:

```bash
cd ~/simple_turtlebot4
source /opt/ros/humble/setup.bash
source install/setup.bash
```

## 2. Mapping

Terminal 1 mở Gazebo, RViz2 và SLAM:

```bash
ros2 launch "$PWD/launch/slam_toolbox.launch.py" mode:=mapping
```

Terminal 2 undock, đợi `SUCCEEDED`, rồi chạy teleop:

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.3 -p turn:=0.5
```

`i`: tiến; `j`/`l`: quay; `k`: dừng. Theo dõi `/map` trong RViz.

Thoát teleop bằng Ctrl+C, giữ SLAM chạy rồi lưu map (ghi đè map chính):

```bash
ros2 run nav2_map_server map_saver_cli -f "$PWD/maps/map" --fmt pgm \
  --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0
```

## 3. Localization / xem map đã lưu

Ctrl+C dừng phiên mapping, đợi Gazebo/RViz đóng rồi chạy:

```bash
ros2 launch "$PWD/launch/slam_toolbox.launch.py" mode:=localization map:="$PWD/maps/map.yaml"
```

Trong RViz, dùng **2D Pose Estimate** đặt vị trí/hướng robot tương ứng Gazebo.
Điểm LiDAR phải khớp tường và vật cản. Nếu chỉ xem map, không cần đặt pose.

## 4. Navigation bằng Nav2

Đóng phiên cũ rồi chạy:

```bash
ros2 launch "$PWD/launch/slam_toolbox.launch.py" mode:=navigation map:="$PWD/maps/map.yaml"
```

Đặt **2D Pose Estimate**, undock ở terminal 2 như trên và dừng teleop.
Chọn **Nav2 Goal** trên RViz, click điểm trống rồi kéo mũi tên đặt hướng đích.
**Global Plan** hiển thị đường đi; **Cancel** trong panel Navigation 2 hủy goal.
