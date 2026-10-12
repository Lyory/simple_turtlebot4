# TurtleBot 4 – Maze, SLAM và localization

Launch duy nhất: `launch/slam_toolbox.launch.py`.
World `worlds/maze_fast.sdf` giữ nguyên bố cục, kích thước và vị trí vật cản của
maze gốc TurtleBot 4. Chỉ tắt bóng đổ và đổi bước vật lý từ 0,003 lên 0,005 s
(200 bước/giây mô phỏng) để giảm tải. Bước lớn hơn làm mô phỏng vật lý thô hơn;
chưa đo hiệu quả hoặc kiểm tra chuyển động sau thay đổi.
Gazebo server/GUI dùng OGRE2 trên NVIDIA; RViz vẽ 15 FPS, tắt display camera.
Robot spawn (0, 0), yaw pi, dock giữ hướng đã đảo.

## Chuẩn bị workspace

Cần môi trường ROS 2 Humble, Ignition Gazebo Fortress và dependency TurtleBot 4.
Mã nguồn simulator có sẵn trong `src/turtlebot4_simulator`; giữ giấy phép Apache 2.0
của upstream trong thư mục đó. Xem hướng dẫn cài dependency tại
`src/turtlebot4_simulator/README.md`.

Sau khi clone vào workspace (các lệnh bên dưới dùng `/root/hri/week4` trong container), build:

```bash
cd /root/hri/week4
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

`build/`, `install/`, log và cache được tạo lại trên máy chạy, không đưa vào Git.
Bản đồ chính trong project là `maps/map.yaml` và `maps/map.pgm`, được đổi tên từ
bản `maze_user` bạn đã quét.

## Mở mô phỏng và mapping

Đóng phiên cũ trước khi chạy. Trong container:

```bash
source /opt/ros/humble/setup.bash
source /root/hri/week4/install/setup.bash
ros2 launch /root/hri/week4/launch/slam_toolbox.launch.py mode:=mapping
```

Để vào container từ host:

```bash
docker exec -it -e XAUTHORITY=/tmp/tb4.Xauthority hri bash
```

Launch mở Gazebo, robot/controller có sẵn, SLAM Toolbox và RViz2.
SLAM bắt đầu sau 15 giây. Robot không tự di chuyển.

## Terminal 2 – teleop

```bash
docker exec -it hri bash
source /opt/ros/humble/setup.bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
```

Đợi `SUCCEEDED`, rồi:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p speed:=0.3 -p turn:=0.5
```

`i`: tiến; `j`/`l`: quay; `k`: dừng. Đi chậm ở góc rẽ.
Tăng speed lên 10 m/s không giải quyết mô phỏng chậm vì controller giới hạn
vận tốc (tối đa 0,46 m/s và motion_control có thể giới hạn thấp hơn).

Kiểm tra giới hạn:

```bash
ros2 param get /motion_control max_speed
```

Số phần trăm ở góc Gazebo là tốc độ mô phỏng so với thời gian thực, không
phải GPU utilization. Nếu RTF là 20%, lệnh 0,3 m/s chỉ đi khoảng 0,06 m mỗi
giây thực. GPU hỗ trợ render cảm biến/GUI; vật lý vẫn tiêu tốn CPU.
Không thể bảo đảm RTF 100% chỉ bằng tăng lệnh vận tốc.

## Lưu map mới

Giữ launch chạy, thoát teleop rồi:

```bash
ros2 run nav2_map_server map_saver_cli -f /root/hri/week4/maps/map --fmt pgm --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0
```

## Localization

Đóng phiên mapping rồi mở lại cùng môi trường với map bạn vừa lưu:

```bash
ros2 launch /root/hri/week4/launch/slam_toolbox.launch.py mode:=localization map:=/root/hri/week4/maps/map.yaml
```

Để localization với map bạn đã lưu:

```bash
ros2 launch /root/hri/week4/launch/slam_toolbox.launch.py mode:=localization
```

Dùng **2D Pose Estimate** trong RViz để đặt vị trí/hướng tương ứng Gazebo.
Map mặc định: `/root/hri/week4/maps/map.yaml`.
Không dùng map small_maze hoặc hành lang cũ cho môi trường maze.

## Navigation bằng Nav2 Goal

Đóng phiên mapping/localization trước khi mở phiên navigation:

```bash
ros2 launch /root/hri/week4/launch/slam_toolbox.launch.py mode:=navigation map:=/root/hri/week4/maps/map.yaml
```

Chế độ này mở Gazebo cùng world maze, RViz, map_server, AMCL và Nav2 bằng
launch/config có sẵn của TurtleBot 4. Không chạy SLAM.
Sau khoảng 15 giây, đặt **2D Pose Estimate** trên RViz đúng vị trí/hướng robot.
Đợi điểm LiDAR khớp tường và vật cản. Ở terminal khác, undock:

```bash
ros2 action send_goal /undock irobot_create_msgs/action/Undock '{}'
```

Đợi `SUCCEEDED`. Dừng teleop hoặc tiến trình đang gửi `/cmd_vel` trước khi
navigation. Chọn **Nav2 Goal** trên RViz, click một vị trí trống trên map,
kéo mũi tên đặt hướng cuối rồi thả. Ban đầu chọn goal gần, cùng hành lang.
RViz sẽ hiển thị đường đi/costmap; robot tự đi đến goal. Dùng **Cancel** trong
panel **Navigation 2** để hủy goal.

Nếu robot chưa di chuyển, kiểm tra các node đã active và action có server:

```bash
ros2 lifecycle get /amcl
ros2 lifecycle get /controller_server
ros2 lifecycle get /planner_server
ros2 lifecycle get /bt_navigator
ros2 action info /navigate_to_pose
```

Nếu thiếu nút Nav2 Goal: dùng nút dấu + trên thanh công cụ RViz và chọn
`nav2_rviz_plugins/GoalTool`. Fixed Frame phải là `map`.
Tài liệu: https://turtlebot.github.io/turtlebot4-user-manual/tutorials/navigation.html

## Đường đi và tránh dock khi navigation

RViz có **Global Plan** (màu xanh lá, `/plan`) để hiển thị đường đi toàn tuyến,
và **Local Plan** cho quỹ đạo ngắn. Mũi tên Nav2 Goal chỉ là pose mục tiêu.
Nếu không thấy đường sau khi gửi goal, xem status Global Plan hoặc chạy:

```bash
ros2 topic echo /plan --once --field poses
```

Nav2 dùng `config/nav2.yaml`, bổ sung ObstacleLayer từ camera depth
`/oakd/rgb/preview/depth/points` vào cả local/global costmap. Chỉ điểm cao
0,02–1,5 m được đánh dấu, giảm khả năng coi sàn là vật cản. Bản đồ/costmap
vẫn 2D; point cloud chỉ là nguồn nhận biết vật cản thấp LiDAR có thể bỏ sót.
Robot radius 0,20 m; inflation radius 0,55 m để tăng khoảng tránh.
Camera hướng về phía trước, có khoảng gần không quan sát được; đây không
phải bảo đảm nhận biết dock từ mọi hướng.

Sau khi khởi động lại navigation, đặt initial pose và undock trước khi gửi goal.
Kiểm tra dock có xuất hiện thành vùng vật cản/inflation trong costmap khi camera
nhìn về phía dock. Có thể dùng teleop quay robot trước khi gửi goal, rồi dừng teleop.

```bash
ros2 topic info /oakd/rgb/preview/depth/points
ros2 topic echo /oakd/rgb/preview/depth/points --once --field header
```

Nếu dock chưa xuất hiện trong costmap, chưa xác nhận được khả năng tránh dock;
không nên thử goal đi xuyên vị trí dock. Các thay đổi chưa được chạy thử tự động.
