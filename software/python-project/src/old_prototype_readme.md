# Python Prototype: Ball Tracking and Prediction

## What This Prototype Is Supposed To Do

This prototype is a single Python script that processes a ZED `.svo2` recording and tries to follow a rolling tennis ball in 3D.

The intended pipeline is:

1. Read RGB frames and depth maps from the ZED recording.
2. Detect the tennis ball in each RGB frame with YOLOv8.
3. Convert the ball's 2D image position into a 3D point using depth.
4. Track the ball across frames.
5. Estimate velocity from recent motion.
6. Predict where the ball will be `0.5` seconds in the future.
7. Save both a CSV log and an annotated output video.

## Mental Model

The prototype works like this:

`SVO2 file -> ZED frame reader -> YOLO detector -> depth-to-3D projection -> tracker -> motion prediction -> CSV/video outputs`

## What The Code Does Right Now

The current script in [prototype.py](/home/vladi/Desktop/obstacle_prediction/software/python-project/src/prototype.py:1) successfully does the following:

- Opens a ZED `.svo2` file with `pyzed`.
- Uses the ZED depth mode defined in `prototype.py`, currently `PERFORMANCE`, to reduce GPU memory usage.
- Reads each frame's RGB image and depth map.
- Runs `yolov8n.pt` and keeps only detections from the COCO `sports ball` class.
- Projects the detection center into 3D using the provided ZED intrinsics.
- Falls back to nearby valid depth values when the exact center pixel has invalid depth.
- Tracks detections using a simple nearest-neighbor tracker.
- Uses a single-ball tracking policy so the prototype prefers one continuous ball track instead of multiple parallel IDs.
- Uses a more forgiving 3D distance threshold when reacquiring the same ball after short detection gaps.
- Estimates velocity from recent 3D positions.
- Predicts a future 3D position using a constant-velocity model.
- Writes:
  - `output_detections.csv`
  - `output_video.mp4`
  - example debug frames in `debug_frames/`
- Prints per-frame stats such as frame id, number of detections, number of active tracks, and inference time.

## Main Parts Of The Script

- `FrameExtractor`
  - Opens the SVO2 file and returns RGB plus depth for each frame.
  - Uses the depth mode set in `prototype.py`, currently `PERFORMANCE`.

- `BallDetector`
  - Runs YOLO on the RGB frame and returns bounding boxes for `sports ball`.

- `Projector3D`
  - Converts the 2D bounding-box center into `(X, Y, Z)` in millimeters.
  - Uses fallback depth sampling if the center pixel is invalid.

- `CentroidTracker`
  - Matches detections frame-to-frame using distance thresholds.
  - Treats the scene as a single-ball problem and keeps one active ball track at a time.
  - Keeps short track history and allows a few missed frames.
  - Uses a looser 3D matching threshold when reconnecting to the same ball after a miss.

- `PhysicsPredictor`
  - Uses recent positions to estimate velocity.
  - Predicts the ball position `0.5s` ahead.

- `Visualizer`
  - Draws detections, track history, labels, and predicted path.
  - Saves the annotated output video.

## What It Does Well Enough For A Prototype

- It can process a real ZED recording end-to-end.
- It can produce non-empty CSV and video outputs.
- It can detect and track the ball for part of the clip.
- It is good enough to test the overall structure of the pipeline.

## What It Does Not Do Reliably Yet

This is still a prototype, so several parts are basic or unstable:

- Detection is not robust on every frame.
  - Small or blurry balls can be missed.

- Tracking is simple.
  - It uses nearest-neighbor matching only.
  - It can create duplicate tracks for the same ball.
  - It can lose the ball after several missed detections.

- Prediction is simple.
  - It assumes constant velocity only.
  - It does not model acceleration, rolling friction, or more advanced motion behavior.

- Depth is approximate.
  - It uses the bounding-box center and nearby fallback values.
  - It does not estimate the ball surface geometry.

- Video export is practical rather than polished.
  - In the current container setup, the output uses a fallback codec if H.264 is not available.

## What It Definitely Does Not Do

The prototype does not currently:

- guarantee one perfect continuous track across the whole clip
- recover robustly from long occlusions or re-entry
- use a custom model trained specifically for tennis balls
- provide accuracy validation against ground-truth labels
- guarantee real-time performance in every environment

## Short Summary

This prototype already demonstrates the full idea:

- read ZED video
- detect the ball
- estimate 3D position
- track over time
- predict future motion
- save CSV and video outputs

What is still missing is reliability and refinement, especially in detection stability, track continuity, and motion modeling.
