# Dynamic Obstacle Detection and Prediction

# Autonomous Robots Research Document

### Author: Vladislav Stefanov

### Fontys University of Applied Sciences

### Eindhoven

## March 20th, 2026

---
# Version History
| Version | Date       | Ammendment                                        |
| ------- | ---------- | ------------------------------------------------- |
| 1.0     | 20.03.2026 | First version of the document - basic terminology |
| 1.1     | 18.04.2026 | Extended terminology. Completion of the document  |

---
# Autonomous Navigation

Autonomous navigation is the capability of machines, such as robots and autonomous vehicles, to plan their path and execute movement without human intervention, utilizing data captured from onboard sensors and sometimes remote navigation aids. This process involves perceiving the environment and moving through it with minimal or no human input. The interdisciplinary nature of autonomous navigation encompasses artificial intelligence, robotics, sensor data processing, and control systems, as these systems integrate sensors to provide environmental perception and process this information through AI algorithms for path-planning and obstacle avoidance. The evolution of autonomous navigation technologies has roots in robotics, aviation, and automotive industries, with early research focusing on machines capable of performing tasks independently and later expanding to mobile robotics and unmanned vehicles capable of navigating dynamic environments. Autonomous navigation includes:
1. Perception and sensing
2. Localization and mapping
3. Path planning and decision making
4. Control systems

---
# Embodied AI

Physical AI is the umbrella term for AI that interacts with the physical world (e.g., robots). Embodied AI is a specialized subset of this area, focusing on systems where the AI's "body" (physical or simulated) is critical for its learning, perception, and reasoning. Embodied AI refers to the integration of artificial intelligence into physical systems, enabling them to interact with the physical world. These systems can include general-purpose robots, humanoid robots, autonomous vehicles (AVs), and even factories and warehouse facilities. The fusion of machine learning, sensors, and computer vision lets these systems perceive, reason, and act in real-world environments.

![Embodied AI overview](embodied_ai_overview.png)

The diagram represents the **sense–think–act loop**, showing how a robot interacts with its environment through a continuous feedback cycle.
- **Perception** receives data from the world via sensors (e.g., cameras, LiDAR, depth sensors). It converts raw signals into structured information such as objects, positions, or maps.
- **Cognition** processes this information. It includes reasoning, planning, and decision-making. Based on the perceived state, the system determines what action should be taken.
- **Action** executes the decision through actuators (motors, controllers), affecting the physical world.

The world is both input and output: it provides observations to perception and is modified by the robot’s actions. This creates a closed loop where each action changes future perception.

This loop runs continuously in real time. In autonomous systems, performance depends on how accurately perception models the world, how effectively cognition plans, and how reliably actions are executed under uncertainty.

---
# Object Manipulation

Includes:
- **Grasping**: holding various objects securely.
- **Complex manipulation**: performing intricate tasks (e.g., assembling components or folding clothes).

---
# Human-Robot Interaction

Recent advancements revolutionized how robots interact with humans, including:
- **Natural language processing**: enabling communication between humans and robots using spoken or written language.
- **Collaboration**: allowing robots to work alongside humans in various shared tasks, from manufacturing to healthcare facilities.

The advent of large language models has further enhanced human-robot interaction. These models have significantly improved the ability of robots to understand and respond to complex commands and queries, making interactions more natural and intuitive.

---
# Robotics Integration

The core of robotic systems lies in the seamless collaboration of hardware and software components. This integration process involves:
- **Hardware components**: sensors, actuators, and other physical parts that enable the robot to interact with its environment.
- **Software systems**: programs and algorithms that control the robot’s behavior and decision-making process.

The goal is to create a cohesive system where all parts work together, enabling complex operations and communication within the robot.

---
# Simulation and Testing

Simulated environments, such as NVIDIA Isaac Sim, NVIDIA Isaac Lab, or Gazebo, can help to validate the entire system before deploying it in real-world scenarios. Additionally, various testing frameworks, such as hardware-in-the-loop (HIL) testing, software-in-the-loop (SIL) testing, unit testing and system-level testing, can be utilized and are commonly used among developers.
## Software-in-the-Loop (SIL)  

SIL is a testing method where the control software is executed in a fully simulated environment without using real hardware. The software typically runs on a host computer, and all inputs and outputs are modeled, allowing developers to validate algorithms, logic, and functional behavior early in development. It is fast, low-cost, and suitable for debugging, but it does not capture hardware-specific effects such as timing constraints or electrical behavior.
## Hardware-in-the-Loop (HIL)

HIL is a testing approach where the actual embedded hardware (such as a controller or ECU) is connected to a real-time simulation of its environment. The hardware interacts with simulated sensors and actuators in a closed loop, enabling realistic testing of timing, I/O behavior, and system integration. It is more complex and expensive than SIL but is essential for validating how the real device behaves under near-real conditions before deployment.

---
# Development Frameworks

Robotics development often relies on specialized platforms and frameworks, such as ROS (Robot Operating System), which provides a flexible environment for writing robot software. Other middleware operating systems can also be used.

---
# Hardware Integration

The goal for hardware integration is to combine various hardware components to function seamlessly as a cohesive system, in order to ensure reliable and efficient interaction between sensors, actuators and controllers.

The integration process involves ensuring that all hardware components work together efficiently for reliable operation across the entire robotic system and efficient data processing for real-time decision making. By focusing on these aspects, hardware integration enables robots to perform complex tasks with precision and adaptability.

## Sensors

Sensors are vital for environmental perception, navigation assistance, and providing feedback for control systems. Common types include:
- **Cameras**: for visual input
- **LIDAR**: for distance measurement
- **IMU (Inertial Measurement Unit**): for orientation
- **GPS**: for location tracking

## Actuators

Actuators enable movement and manipulation, applying force and making adjustments based on sensor feedback. Types of actuators include:
- **Motors**: DC and stepper motors for movement
- **Servos**: for precise position control
- **Pneumatic and hydraulic actuators**: for force application

## Controllers

Controllers process sensor data, execute control algorithms, and facilitate communication among components. Examples include:
- **Microcontrollers**: such as Arduino and PIC
- **Single-board computers**: like Raspberry Pi and NVIDIA Jetson
- **Embedded systems**: for integrated control solutions

---
# Autonomy Software Architecture

![Autonomy software architecture](auto_software_arch.png)

This diagram provides an overview of a relatively complex autonomy software architecture, often used in applications like robotaxis. It illustrates the integration of various components essential for autonomous systems, though some robots may only use a subset of these elements.

- **Perception and localization**: utilizes sensors such as cameras and LIDAR, along with mapping systems, to assess the environment and determine the robot’s position and state.
- **Planning** involves multiple stages:
    - **Global planning**: similar to setting a route on a map, defining the mission and waypoints to reach a goal.
    - **Behavior planning**: determines actions, such as which object to manipulate and how.
    - **Local planning**: generates trajectories for specific tasks, guiding the robot through precise paths.
- **Control and actuation**: the controller tracks trajectory states to execute movements, whether for manipulation or navigation. Outcomes are tested in both virtual simulations and real-world scenarios.
- **Feedback loop**: continuously gathers data from sensors and localization to refine planning and improve system performance. This iterative process ensures adaptive and responsive robot behavior.

---
# Sensing

Sensing is crucial for enabling autonomous robots to understand their environment. This overview explores the different types of cameras and sensors used in robotics, highlighting their unique advantages and applications.

### Types of Cameras

- **Monocular cameras:** single-lens cameras that capture 2D images. They are simple, cost-effective, and widely available, making them ideal for basic object detection, image recognition, and simple navigation tasks.
- **Stereo cameras**: use two lenses to capture images simultaneously, mimicking human binocular vision. This setup provides depth perception and 3D information, useful for obstacle avoidance and 3D mapping (e.g., the Hawk 3D depth camera). A stereo camera CAN be an RGB-D camera if it outputs both color and depth.
- **RGB-D cameras**: combine standard RGB color imaging with depth sensing to provide robust 3D perception. These cameras are beneficial for advanced navigation, object manipulation, and interaction. The Intel RealSense stereo RGB-D camera is a popular choice.
- **Thermal cameras**: detect infrared radiation to create images based on temperature differences. They are effective in dark environments or through smoke and fog, making them valuable for search, rescue, and surveillance operations.
- **Event-based cameras**: offer high temporal resolution and low latency, ideal for high-speed motion detection and tracking.

### Types of Lidar

- **2D Lidar**: simpler, cheaper, and faster, but with limited functionality. Ideal for basic planar navigation and obstacle detection.
- **3D Lidar**: provides detailed spatial information, a wide field of view, and high resolution, making it suitable for autonomous vehicle mapping. However, it is generally more expensive than cameras.
- **Solid-state, flash, and MEMS Lidar**: Offer durability and cost-effectiveness, using laser pulses to measure distances and create detailed maps.

### Other Common Sensors

- **Ultrasonic sensors**: emit sound waves to measure distance based on echo return time. Affordable and commonly used in low-cost robots like home vacuum cleaners.
- **Radar**: reliable in diverse conditions, providing distance, speed, and size information. Used in applications like robotaxis.
- **GPS**: essential for outdoor localization.
- **IMU (Inertial Measurement Unit)**: measures acceleration and rotational rates to track motion and orientation. Widely used in mobile robots.
- **Wheel encoders**: Measure wheel rotation to determine travel distance.
- **Magnetic sensors (compasses)**: detect the Earth’s magnetic field to determine orientation and provide heading information.
- **Environmental sensors**: measure temperature, humidity, and air quality.
- **Touch sensors**: cost-effective and useful for detecting contact, commonly used in household robots.

These sensors collectively enhance a robot’s ability to perceive its surroundings and make informed decisions based on real-time data.

---
# Perception

In the world of robotics, perception is crucial for enabling autonomous robots to understand their environment. Just as humans use a combination of senses like sight, hearing, and touch to interpret the world around them, robots rely on sensor fusion. This process integrates data from multiple sensors to create a comprehensive and accurate representation of the environment.

## Key Components of Perception

- **Sensor fusion**: combines data from various sensors to provide a holistic view of the surroundings.
- **Object detection and recognition**: identifies and classifies objects within the robot’s environment.
- **Object tracking**: continuously follows an object as it moves, similar to how our eyes track moving objects.
- **Scene understanding**: interprets the overall context of the environment, allowing robots to make informed decisions.

The Isaac Perceptor leverages technologies like VSLAM (Visual Simultaneous Localization and Mapping) for accurate odometry and NVBlox for detailed 3D reconstruction.

---
# Localization and Mapping

Localization and mapping are essential for robots to navigate and interact with their environment effectively. Imagine a robot as a traveler who needs a map and a compass to explore unfamiliar territory. These processes enable the robot to determine its position and create a map of its surroundings.

## The Importance of Localization

Localization helps robots identify their position within an environment, allowing them to make informed decisions. For instance, in tasks like trajectory tracking, knowing the exact location is crucial to ensure the robot follows the intended path accurately.
- **GPS (Global Positioning System)**: used primarily outdoors to provide location data.
- **Visual odometry**: utilizes camera images to estimate movement, turning the task into a computational problem.
- **Lidar-based localization**: Matches current positions with pre-existing maps using laser-based sensors.

## Mapping Techniques

Mapping involves creating a representation of the environment, which is vital in large spaces like warehouses or factories.
- SLAM (Simultaneous Localization and Mapping): a technique where robots simultaneously build a map and track their location within it.
- Occupancy grids: represent environments as grids, with each cell indicating the probability of being occupied.

These techniques are foundational for autonomous navigation, allowing robots to understand and interact with their environments effectively. 

---
# Navigation and Path Planning

In autonomous mobile robotics, navigation and path planning are important to ensure that robots can move efficiently and safely through their environments. This involves several layers of planning, each with a specific focus.

## Classical Navigation Systems

### Routing and Mission Planning

Routing and mission planning determines the preferred route over map networks. It commonly uses algorithms including A*, D*, and RRT (Rapidly-exploring Random Tree). This is similar to getting directions at an intersection - deciding whether to go straight or turn.

#### Motion Planning

Motion planning generates a sequence of movements that allow robots to follow a planned path while avoiding obstacles. It usually takes a few seconds to process both components, decision making and trajectory generation.
- **Decision making**: focuses on behavior planning and interactions, such as deciding whether to navigate around obstacles like pallets or yield to moving forklifts.
- **Trajectory generation**: involves creating a time-based trajectory, detailing speed, acceleration, and heading angles for precise control.

#### Obstacle Avoidance

- **Real-time detection**: ensures functional safety by detecting and avoiding obstacles in real time.
- **Reactive navigation**: uses sensors to make immediate adjustments, acting as a backup when the main autonomy system fails to detect obstacles.

This layered approach allows robots to interact dynamically with their environment, executing complex navigation tasks effectively. 

---
# Control Systems in Robotics

Once a robot’s trajectory and target states are defined, the control system translates this information into commands for the robot’s actuators. This ensures that the robot follows the planned path accurately.

## Feedback Control

Feedback controls adjust the robot’s actions based on sensor input to achieve desired behaviors.

A common method for feedback control is PID control (Proportional-Integral-Derivative). PID control is a widely used algorithm that minimizes the error between desired and actual positions by continuously adjusting movements. It operates by comparing the desired trajectory states with actual states obtained from localization data and making real-time corrections.

## Trajectory Tracking

You can use trajectory tracking to ensure the robot accurately follows a planned trajectory.

One commonly used method is MPC (Model Predictive Control). MPC is an advanced control strategy that optimizes the robot’s path using a predictive model of its behavior. MPC is more sophisticated than PID control and is often used for precise trajectory tracking and whole-body control in humanoid robots.

These control methods are essential for ensuring that robots can navigate their environments effectively, maintaining accuracy and safety in their movements.

---
# Foundation Models

Foundation models are transforming robotics by enhancing capabilities in perception, decision-making, and control. These models, pre-trained on vast datasets, offer superior adaptability and generalization compared to traditional methods.

## Key Areas of Application

- **Robot policy learning**: techniques like diffusion policies, language-conditioned imitation learning, and reinforcement learning improve data efficiency and contextual understanding. These models help robots learn optimal actions through language-driven rewards.
- **Value learning**: instead of directly learning policies, robots learn value functions to choose actions with the lowest cost, enhancing decision-making processes.
- **High-level task planning**: foundation models enable cognitive-level planning for complex tasks. For example, humanoid robots can understand high-level instructions like picking up a specific box by leveraging these models.
- **LLM-based code generation**: large language models (LLMs) generate code for robot training and execution. This capability is exemplified by systems like GenSim, which create task simulations for various applications.

## Advanced Techniques

- **Open vocabulary object detection and 3D classification**: models like Dino V2 enhance encoding capabilities for diverse objects without predefined categories, crucial for dynamic environments.
- **Semantic segmentation**: open-vocabulary segmentation allows robots to recognize and interact with previously unseen objects, expanding their operational scope.
- **3D representation and affordance**: foundation models offer open-vocabulary 3D representations, enabling robots to infer object affordances - deciding how to interact with objects based on their properties.

---
# Physical AI and Simulation

Physical AI (or embodied AI) systems like Voyager and MineDojo simulate tasks to train robots in both virtual and real-world settings. These systems leverage foundation models to improve task execution and adaptability.

Foundation models are paving the way for more intelligent and versatile robotic systems, capable of performing complex tasks with minimal human intervention.

## NVIDIA Cosmos

![](https://learn.learn.nvidia.com/assets/courseware/v1/6bf51975da8d616117b3278175e12ce5/asset-v1:DLI+S-OV-35+V1+type@asset+block/NVIDIA-Cosmos.jpg)

NVIDIA Cosmos is a world foundation model designed to accelerate the development of physical AI systems, including robots and autonomous vehicles. Cosmos introduces a family of world foundation models (WFMs) that are purpose-built for generating physics-aware videos and world states.

World foundation models are neural networks that can predict and generate physics-aware virtual environments. These models are trained on vast amounts of data. Cosmos WFMs offer developers an efficient way to generate massive amounts of photoreal, physics-based synthetic data. This capability significantly reduces the time and cost associated with training and evaluating physical AI models.

NVIDIA Cosmos represents a significant leap forward in physical AI and robotics development. By providing powerful world foundation models and tools, it promises to accelerate innovation in autonomous vehicles, robotics, and other physical AI applications, potentially ushering in a new era of intelligent machines.

## Mobility Foundation Model

![](https://learn.learn.nvidia.com/assets/courseware/v1/a54de229499ad981cf48a18d0cebf69a/asset-v1:DLI+S-OV-35+V1+type@asset+block/Artboard_4.png)

The Mobility Foundation Model acts as a central “brain” for robotic systems, processing robust vision states and generating word modeling and action policies. This model is designed to work across various robotic embodiments, including Autonomous Mobile Robots (AMRs).

Key Features
- **Simulation-based training**: the model is trained using only simulation data, allowing for efficient development without physical trials.
- **Zero-shot deployment**: successfully deployed in real-world environments like the Hubble Lab without additional training, demonstrating its adaptability.
- **Cross-embodiment capability**: policies developed for AMRs are transferable to other robots, such as humanoid robots, quadrupeds, and space forklifts.

This model exemplifies the potential for cross-platform functionality in robotics, addressing complex computational challenges and paving the way for versatile applications.

---
# VLM, LLM and RAG for Robotics

The integration of Vision Language Models (VLM), Large Language Models (LLM), and Retrieval-Augmented Generation (RAG) is transforming robotics through a concept known as incidental perception. This approach allows robots to build and utilize memory to navigate and interact with their environment effectively.

Key Features
- **Memory building**: robots use these models to remember events, locations, and times, enabling them to return to specific places when needed.
- **Demo example**: in a recent NVIDIA office demo, a robot was instructed to find a “nice view.” It recalled previous observations, such as greenery, and guided the user to that location.
- **Task execution**: the robot can perform tasks like fetching items based on memory. For instance, it can locate chips in a kitchen by remembering where they were previously seen.

## Technology Components

- **Video Language Model (VLM)**: captures and captions video data every few seconds, storing this information in a vector database for long-term memory.
- **Speech processing**: utilizes NVIDIA’s Vsper for converting speech into text, enhancing interaction capabilities.
- **Open vocabulary learning**: Allows the robot to understand and respond to new and diverse queries without predefined categories.

The integration of VLM, LLM, and RAG enables robots to have extended memory and improved interaction capabilities, paving the way for more intuitive and responsive robotic systems.

---
# Open Challenges in Robotics

While foundation models offer significant advancements, several challenges remain in robotics:
- **Data scarcity**: training models require vast amounts of data, which is often limited in robotics. NVIDIA’s tools like Isaac Sim and Isaac Lab help address this by simulating environments to generate data.
- **Real-time performance**: deploying foundation models in real-time is crucial. Technologies like NVIDIA’s Orin enable on-device processing, reducing reliance on cloud computing and enhancing performance.
- **General purpose perception**: achieving a truly general perception system that can handle diverse tasks and environments remains challenging.
- **Unified representation**: integrating multi-modal inputs (e.g., visual, auditory) into a cohesive understanding is complex but essential for robust robot behavior.
- **Robustness and safety**: evaluating and ensuring the safety and reliability of robots in unpredictable situations is vital. Tools like OSMO (software-in-the-loop and hardware-in-the-loop) aid in this evaluation process.
## Opportunities

- **On-edge deployment**: running models directly on devices enhances performance and reduces cloud dependency.
- **Benchmark development**: creating benchmarks helps compare algorithms across scenarios, improving reproducibility and performance assessment.
- **Human-robot interaction**: enhancing social navigation and understanding human expectations improves collaboration between humans and robots.

These challenges present opportunities for innovation, driving the development of more capable and adaptable robotic systems.

---
# References

A Beginner's Guide to Autonomous Robots - Nvidia
https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-OV-35+V1

Nvidia Glossary
https://www.nvidia.com/en-us/glossary/

Understanding Sensor Fusion and Tracking by Matlab - YouTube
https://youtube.com/playlist?list=PLn8PRpmsu08ryYoBpEKzoMOveSTyS-h4a&si=waFRcquUgr6DjGmW

Autonomous Navigation - ScienceDirect
https://www.sciencedirect.com/topics/computer-science/autonomous-navigation

Voyager: An Open-Ended Embodied Agent with Large Language Models
https://voyager.minedojo.org/

MineDojo
https://minedojo.org/

Nvidia Cosmos
https://www.nvidia.com/en-us/ai/cosmos/