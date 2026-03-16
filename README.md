# Dynamic Obstacle Detection and Prediction

## Context

This project is conducted within the High Tech Embedded Software (HTES) research group at Fontys University of Applied Sciences in Eindhoven. The group focuses on applied software research for high-tech embedded systems and mobile robotics. :contentReference[oaicite:0]{index=0}

Several robotics projects within HTES share a common limitation: the lack of a reliable system for detecting, tracking, and predicting the motion of dynamic obstacles using 3D depth perception. Existing systems rely mainly on classical perception pipelines and reactive obstacle avoidance, while recent AI-based approaches such as world models have not yet been systematically explored in this context. :contentReference[oaicite:1]{index=1}

The goal of this project is to design and evaluate a modular perception pipeline that can be reused across different HTES robotics platforms such as the Brum (Self-Driving Challenge), Jackal UGV, Boomba triangular robot platform, and Avular Origin One. :contentReference[oaicite:2]{index=2}


## Problem Description

Mobile robots operating in dynamic environments must perceive moving objects and anticipate their behavior to operate safely and effectively. Current systems in the HTES context primarily detect obstacles from depth sensors but lack robust mechanisms for tracking objects and predicting their motion. :contentReference[oaicite:3]{index=3}

The core problem is the absence of an object-centric perception pipeline capable of:

- Detecting arbitrarily moving objects from depth data  
- Maintaining consistent object identities over time (multi-object tracking)  
- Predicting short-term future motion of those objects  

Without motion prediction, robotic systems react only to the current state of the environment. This limits the ability of navigation and planning modules to anticipate changes in dynamic scenes. Technical challenges include noisy depth data, point-cloud segmentation under clutter or occlusions, reliable data association across frames, and maintaining real-time performance. :contentReference[oaicite:4]{index=4}


## Solution Overview

The project proposes the development of a modular 3D perception and motion prediction pipeline. The system converts raw 3D sensor data (e.g., depth cameras, LiDAR, RGB-D) into structured information about dynamic obstacles. :contentReference[oaicite:5]{index=5}

The pipeline consists of three main components:

1. **Detection** – identifying object-level entities from 3D sensor data  
2. **Tracking** – maintaining stable object identities across frames  
3. **Prediction** – estimating short-term future motion with quantified uncertainty  

The architecture is designed to be modular so that different detection, tracking, or prediction methods can be evaluated and replaced independently. The implementation is expected to support real-time or near-real-time operation and integrate with robotics software stacks such as ROS2. :contentReference[oaicite:6]{index=6}


## Expected Contribution

The project aims to provide the following contributions:

- A modular perception pipeline for detecting, tracking, and predicting dynamic obstacles  
- An empirical comparison between classical robotics methods and newer world-model approaches  
- Experimental validation of the approaches under controlled conditions  
- A reusable perception module that can support multiple HTES mobile robotics projects  

The results are intended to clarify whether world models represent a practical direction for future robotics perception research within the HTES group. :contentReference[oaicite:7]{index=7}


## Preconditions

The project is conducted under several practical constraints:

- Development follows an Agile workflow using a Git issue board  
- Source code is managed using GitLab  
- Experiments may use dedicated compute resources (e.g., the “bigboi” PC)  
- Hardware resources such as depth cameras are available through the ISSD  

These conditions define the technical and organizational environment in which the perception system will be developed and evaluated. :contentReference[oaicite:8]{index=8}