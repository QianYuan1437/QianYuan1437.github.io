---
title: 【安装学习】安装Cartographer ROS（noetic）
date: 2024-11-02 00:00:00
categories:
  - 安装学习
tags:
  - 安装学习
---


# 【安装学习】安装Cartographer ROS（noetic）

## 参考链接：https://google-cartographer-ros.readthedocs.io/en/latest/compilation.html

## 1、创建工作空间

```bash
mkdir -p ~/catkin_google_ws/src
cd catkin_google_ws/src
catkin_init_workspace
```

## 2、安装工具

```bash
sudo apt update
sudo apt install -y python3-wstool python3-rosdep ninja-build stow
```

## 3、初始化工作空间

```bash
cd catkin_google_ws
wstool init src
wstool merge -t src https://raw.githubusercontent.com/cartographer-project/cartographer_ros/master/cartographer_ros.rosinstall
wstool update -t src
```

## 4、安装依赖

```bash
sudo pip install rosdepc
sudo rosdepc init
rosdepc update
```

## 5、Libabsl-dev处理

进行XML文件修改，路径为

```bash
cartographer_ws/src/cartographer/package.xml
```

找到第46行`<depend>libabsl-dev</depend>`删掉

## 6、执行rosdep install命令

```
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro=${ROS_DISTRO} -y
```

## 7、安装abseil库

- 先删除本地abseil库

  ```bash
  sudo apt-get remove ros-${ROS_DISTRO}-abseil-cpp
  ```

- 再运行

  ```bash
  src/cartographer/scripts/install_abseil.sh
  ```

- 这时发现可能会报错，类型如下：

  ```bash
   * existing target is neither a link nor a directory: include/absl/base/internal/sysinfo.h
  ```

- 定位到上方.sh脚本运行后下载的文件夹，与src文件夹同级，进行如下操作：

  ```bash
  cd ~/path/to/abseil-cpp
  mkdir build && cd build
  cmake -DCMAKE_POSITION_INDEPENDENT_CODE=TRUE -DCMAKE_BUILD_TYPE=Release ..
  make -j$(nproc)
  sudo make install
  ```

- 确保编译器可以找到安装的 `abseil-cpp` 库。检查 `LD_LIBRARY_PATH` 和 `CMAKE_PREFIX_PATH` 中是否包含 `/usr/local/lib` 和 `/usr/local`，以确保 CMake 和 linker 能找到 `abseil-cpp` 库。请在终端中执行下方命令，以将这些变量永久添加到 `~/.bashrc` 里：

  ```bash
  echo 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
  echo 'export CMAKE_PREFIX_PATH=/usr/local:$CMAKE_PREFIX_PATH' >> ~/.bashrc
  source ~/.bashrc
  ```

## 8、构建

在 `catkin_ws` 中清理 `build_isolated` 和 `devel_isolated` 文件夹后重新构建：

```bash
cd ~/WS/catkin_ws
rm -rf build_isolated devel_isolated install_isolated
catkin_make_isolated --install --use-ninja
```