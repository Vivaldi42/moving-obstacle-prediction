# Ball Tracking and Prediction Prototype with ZED SDK

## Goal
Build a first prototype that tracks and predicts the motion of a ball using the ZED SDK.  
The prototype should be simple, measurable, and modular so it can later be extended to other object types.  
The long-term goal is a perception pipeline that supports both:
- class-agnostic tracking and prediction
- class-aware tracking and prediction when class information is available

This matches the project direction of a modular pipeline for detection, tracking, and short-term motion prediction, with replaceable components and explicit evaluation.

## What ZED SDK provides
Use ZED mainly for:
- camera capture
- RGB image
- depth map
- confidence map
- per-pixel 3D data / point cloud
- SVO recording and playback

At this stage, do not rely on built-in object classes. The SDK provides the sensor and geometry side; the main ball-specific logic is still custom.

## Minimal architecture
```mermaid
flowchart LR
    A[ZED Camera + SDK] --> B[Ball Detection]
    B --> C[3D State Estimation]
    C --> D[Tracking]
    D --> E[Velocity Estimation]
    E --> F[Prediction]
    F --> G[Output]
````

## Core design choices

### 1. Start class-agnostic

The first version does not need to know that the object is a ball.  
It can simply track "a moving object with a consistent trajectory".

Why:
- class is not required for detection, tracking, or short-horizon prediction
- constant-velocity prediction is enough for an MVP
- this keeps the system generic from the start

### 2. Keep class optional

The system should support an optional class field, not require it.

Example tracked object:

```text
{
  id,
  position_3d,
  velocity_3d,
  confidence,
  class_name: optional
}
```

Why:
- some objects may be classified, others may not
- later class-specific predictors can be used
- the pipeline should still work when classification is missing or uncertain 

### 3. Separate detection from tracking/prediction

Detection should be treated as a replaceable front-end.  
Tracking and prediction should operate on a common object-state format.

Why:
- the ball detector will likely be specific
- later it should be easy to plug in:
    - another detector for generic obstacles
    - body tracking for people
    - class-aware predictors
    
### 4. Prefer a simple baseline first

Start with:
- fixed camera
- one ball
- plain background
- short prediction horizon
- constant-velocity model

Why:
- reduces technical risk
- gives measurable results quickly
- aligns with the project plan to start with simple baselines and increase complexity incrementally

## Suggested first implementation

1. Capture RGB, depth, and confidence from ZED
2. Detect the moving ball in 2D
3. Associate the detection with depth
4. Estimate 3D position
5. Track the object over time
6. Estimate velocity
7. Predict short-term future position
8. Log results and evaluate accuracy, stability, and latency

## Extension path

After the ball prototype works:
1. generalize the detector for other obstacles
2. add optional class labels
3. add class-specific prediction models when useful
4. optionally add a separate human branch using ZED Body Tracking

## Final design principle

Build a **class-agnostic core** with **class-aware extensions**.

This gives:
- a simple and feasible first prototype
- a reusable architecture
- a path toward handling both generic obstacles and specific classes later