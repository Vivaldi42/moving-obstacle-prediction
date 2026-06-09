# Knowledge Gained - VDL RoboCup Team (13.05.2026)

# ROS2 Pixi

https://pixi.prefix.dev/latest/tutorials/ros2/

Pixi provides a modern, reproducible development workflow for robotics applications using ROS2. Using lockfile-based environment management, it enables developers to share consistent software stacks across machines while isolating dependencies from the host system. Pixi unifies C++, Python and ROS 2 packages within a single cross-platform workspace, simplifying setup and development workflows. This allows developers to build and test ROS 2 applications natively across Linux, macOS and Windows without relying on complex manual installations.

# ROS2 Components

https://docs.ros.org/en/lyrical/Concepts/Intermediate/About-Composition.html

ROS 2 Components provide a modular architecture for building applications as dynamically loadable units within a shared process. Unlike ROS 2 nodes that typically run as separate executables, components allow multiple nodes to execute inside a single container process while still preserving the ROS 2 communication model. This reduces inter-process communication overhead, improves memory efficiency, and enables lower-latency data exchange through intra-process communication.

# Robocup Publications

https://robocup.nl/publications.html

Research teams participating in RoboCup publish technical papers describing the systems, architectures and algorithms used in competition-winning robots. These works include developments in vision-based machine learning, semantic strategy frameworks, trajectory planning, humanoid locomotion, reinforcement learning and AI-driven perception systems.

# VDL Robocup Team Publications

https://robotsports.nl/index.php/en/documents/publications-and-downloads

The VDL RobotSports publications page shows the research, software and engineering systems developed for autonomous robotic soccer. The published material covers areas such as real-time object detection, multi-robot coordination, embedded systems, AI-based perception and autonomous gameplay.

# YOLOv5-TensorRT
	
https://github.com/noahmr/yolov5-tensorrt

https://robotsports.nl/images/2021/RoboCup2021_MSL_Scientific_challenge_VDL_robotsports__Low-cost_fast_mobile_object_detection_for_robotic_soccer.pdf

The GitHub repository developed by VDL RobotSports is a high-performance object detection library that accelerates YOLOv5 inference using NVIDIA TensorRT for real-time robotics and computer vision applications. The project provides both C++ and Python APIs, supports FP32/FP16 inference, ONNX model conversion, CUDA-accelerated preprocessing, and deployment on NVIDIA GPUs and Jetson platforms.