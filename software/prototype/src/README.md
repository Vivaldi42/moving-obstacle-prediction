# Prototype Pipeline

This folder contains a small prototype that runs ball detection, 3D position lookup, short-term tracking, and future-position prediction over one ZED `.svo2` recording.

The current implementation is split across:

- `pipeline.py` for reusable helper functions and the Kalman filter
- `main.py` for the end-to-end processing loop

## What The Prototype Does

For each frame in the input recording, the prototype:

1. Opens the next ZED frame.
2. Reads the left RGB image and ZED `XYZ` point cloud.
3. Runs YOLO on the RGB frame and keeps the best `sports ball` detection.
4. Converts the detection center pixel into a 3D point in metres.
5. Uses a constant-velocity Kalman filter to smooth motion in 3D.
6. Fills short detection gaps with Kalman predictions for up to `MAX_MISS = 5` frames.
7. Projects a future predicted 3D position back into image space.
8. Draws the observed trail and predicted point onto the frame.
9. Writes the annotated frame to an output video.

Mental model:

`SVO2 -> RGB + XYZ -> YOLO sports-ball detection -> 3D lookup -> Kalman filter -> future prediction -> annotated video`

## main.py

[`main.py`](/home/vladi/Desktop/obstacle_prediction/software/prototype/src/main.py:1) runs the full loop.

### Current constants

- `SVO_PATH` points to `/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2the`
- `OUTPUT_PATH` is `/app/output_detections.mp4`
- `PREDICTION_HORIZON` is `0.2` seconds
- `MAX_MISS` is `5`
- YOLO weights are loaded from `yolov8x.pt`

### Runtime behavior

On every frame:

- If the Kalman filter has already been initialized, `kf.predict()` advances the state one step.
- YOLO runs on the RGB frame and returns the center pixel of the highest-confidence ball detection.
- If valid 3D data exists at that pixel, the Kalman filter is initialized or corrected with the measured `(x, y, z)` position.
- If YOLO detects the ball but depth is invalid, the code still draws the detection but skips Kalman correction.
- If YOLO misses and the filter is initialized, the prototype projects the Kalman-predicted 3D position back to a pixel for up to `5` missed frames.
- A blue trail shows the most recent image positions.
- A red marker shows the predicted position `0.2` seconds ahead.

### Visualization colors

- Green: YOLO detection with valid 3D position
- Orange: Kalman-only fill-in during short missed-detection gaps
- Blue: recent trajectory history
- Red: future predicted position

### Output

The current code writes:

- `/app/output_detections.mp4` — annotated video

## pipeline.py

[`pipeline.py`](/home/vladi/Desktop/obstacle_prediction/software/prototype/src/pipeline.py:1) holds the reusable pieces.

### `open_svo(path)`

- Opens a ZED SVO2 file for offline playback
- Sets `svo_real_time_mode = False`
- Sets coordinate units to `sl.UNIT.METER`
- Returns an initialized `sl.Camera`

### `get_intrinsics(cam)`

- Reads `(fx, fy, cx, cy)` from the left ZED camera calibration
- These values are used to project 3D points back into image coordinates

### `grab_frame(cam, mat_rgb, mat_xyz)`

- Advances one frame through the SVO file
- Returns:
  - `left_rgb`: RGB image converted from ZED BGRA output
  - `xyz_map`: ZED `sl.MEASURE.XYZ` array
- Returns `None` when the end of the SVO file is reached

Important detail:

- This prototype uses the full `XYZ` point cloud, not a scalar depth map

### `resolve_xyz(xyz_map, cx, cy)`

- Reads `(x, y, z)` directly from the selected pixel
- If the exact pixel is invalid, it searches a local patch with radius `4`
- Uses the median of valid nearby 3D points as fallback
- Returns `None` if no valid nearby 3D point exists

### `project_to_pixel(x, y, z, fx, fy, cx, cy)`

- Projects a 3D point in metres into image coordinates
- Returns `None` when `z <= 0`

### `load_model(weights="yolov8x.pt")`

- Loads a YOLO model from the provided weights path

### `detect(model, left_rgb, classes=None)`

- Runs YOLO on a single RGB frame
- Defaults to COCO class `32`, which is `sports ball`
- Uses `conf=0.25`
- Returns the center pixel `(cx, cy)` of the highest-confidence detection
- Returns `None` if no detection is available

### `BallKalmanFilter`

This is the core motion model used by the prototype.

- State: `[x, y, z, vx, vy, vz]`
- Units: metres and metres per second
- Model: constant velocity

Methods:

- `init(x, y, z)`: seeds the filter with the first 3D observation
- `predict()`: advances the filter one frame
- `correct(x, y, z)`: fuses a new 3D measurement
- `predict_ahead(horizon)`: estimates a future position without modifying the filter state

## What This Prototype Is Good For

- Verifying the end-to-end ZED plus YOLO plus prediction flow
- Visual debugging of ball detections and short-term motion
- Quickly testing whether future-position overlays are plausible

## Current Limitations

- Only the single best ball detection is used each frame
- There is no multi-object tracker
- The motion model is constant velocity only
- Long occlusions are not handled robustly
- Depth fallback is local and approximate
- The output is only an annotated video

## Run Shape

The expected run flow is:

`python src/main.py`

The exact environment still depends on the ZED SDK, model availability, and the container or host setup used for this project.
