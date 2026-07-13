# Dynamic Obstacle Detection and Prediction

## Context

This project was conducted within the High Tech Embedded Software (HTES) research group at Fontys University of Applied Sciences in Eindhoven as a graduation internship. The group focuses on applied software research for high-tech embedded systems and mobile robotics.

Several robotics projects within HTES share a common limitation: the lack of a reliable system for detecting, tracking, and predicting the motion of dynamic obstacles using 3D depth perception. Existing systems rely on reactive obstacle avoidance and do not maintain object-level predictions over time.

The goal of the project was to design, implement, and evaluate a modular 3D depth-based perception pipeline capable of detecting, tracking, and predicting dynamic obstacles in real time for mobile robotics applications.

---

## Problem Description

Mobile robots operating in dynamic environments must perceive moving objects and anticipate their behavior to operate safely and effectively. Current systems in the HTES context primarily detect obstacles from depth sensors but lack mechanisms for tracking objects and predicting their motion.

The core problem is the absence of an object-centric perception pipeline capable of:

- Detecting moving objects from depth data
- Maintaining a consistent object identity over time
- Predicting short-term future motion

Without motion prediction, robotic systems react only to the current state of the environment, limiting the ability of navigation and planning modules to anticipate changes in dynamic scenes.

---

## What Was Built

The project delivered `3dpipe`: a complete 3D detection, tracking, and prediction pipeline using a ZED 2i stereo camera, YOLOv8x object detection, and a Kalman filter. The pipeline runs fully inside Docker and supports both x86 workstations (RTX 4090) and NVIDIA Jetson.

**Pipeline stages:**
1. **Detection** - YOLOv8x detects the object in the RGB frame (COCO class 32, confidence threshold 0.15)
2. **Depth estimation** - 3D position is extracted from the ZED depth map using front-face centroid sampling
3. **Tracking** - a Kalman filter maintains a filtered 3D position and velocity estimate across frames
4. **Prediction** - the filter extrapolates a 0.2-second (6-step) future trajectory

Two Kalman filter motion models were implemented and evaluated:
- **CV (constant-velocity)** - 6-state filter: position + velocity
- **CA (constant-acceleration)** - 9-state filter: position + velocity + acceleration

**Evaluation was structured across four phases:**
- Phases 1-3: swept 4 CV configurations varying process noise
- Phase 4: compared the best CV configuration against 5 CA variants with different acceleration process noise

**Phase 4 results (single sequence, HD1080):**

| Config | ADE (cm) | FDE (cm) |
|---|---|---|
| cv_optimized | 0.72 | 1.10 |
| ca_apn_0.01 | 0.71 | 1.08 |
| ca_apn_0.05 | 0.72 | 1.09 |
| ca_apn_0.1 | 0.73 | 1.11 |
| ca_apn_0.5 | 0.79 | 1.25 |
| ca_apn_1.0 | 0.86 | 1.41 |

The CA model matched the CV model at low acceleration noise but offered no meaningful improvement on smooth trajectories. Higher acceleration noise degraded accuracy.

**Scope decisions:**
- Single-object tracking (one ball); multi-object tracking was not implemented
- ZED 2i only; no LiDAR or RGB-D fusion
- No ROS2 integration; standalone Docker deployment
- World-model approaches were reviewed but not implemented - the classical Kalman filter pipeline was the primary engineering deliverable

---

## Repository Structure

```
3dpipe/                 - Full pipeline implementation, Docker, evaluation, docs
project_organization/   - Project plan, sprint logs, stakeholder info, feedback notes
```

See [3dpipe/README.md](3dpipe/README.md) for setup and run instructions.  
See [3dpipe/docs/project_report/project_report.md](3dpipe/docs/project_report/project_report.md) for the full project report.

---

## Contributions

- A working modular 3D perception pipeline (detection, tracking, prediction) deployable on x86 and Jetson via Docker
- Empirical evaluation of CV vs CA Kalman filter variants across multiple configurations with ADE/FDE metrics
- Full documentation covering system design, Kalman filter derivation, evaluation metrics, and detection accuracy
- A reusable baseline for future HTES perception work - the pipeline is parameterised and designed so that detection, tracking, and prediction stages can each be replaced independently
