# src

## pipeline.py

Reusable functions and classes for the obstacle prediction pipeline. Nothing in here runs on its own.

### `open_svo(path)`
Opens a ZED SVO2 recording file for offline playback. Coordinates are set to metres. Returns an `sl.Camera` object ready to grab frames from.

### `get_intrinsics(cam)`
Reads the left camera intrinsics `(fx, fy, cx, cy)` from the ZED SDK. Used to project 3D positions back onto the image plane.

### `grab_frame(cam, mat_rgb, mat_xyz)`
Advances to the next frame and returns two NumPy arrays:
- `left_rgb` — left camera image, shape `(H, W, 3)`, dtype `uint8`, RGB
- `xyz_map` — dense point cloud, shape `(H, W, 4)`, dtype `float32`, metres. Each pixel holds `(x, y, z, _)` where x=right, y=down, z=depth.

Returns `None` at end of file.

### `resolve_xyz(xyz_map, cx, cy)`
Reads the 3D position at pixel `(cx, cy)` from the point cloud with a two-level fallback:
1. Center pixel — used directly if all three components are finite.
2. 4px radius patch — takes the median of all finite points in the neighbourhood.

Returns `(x, y, z)` in metres, or `None` if no valid depth was found.

### `project_to_pixel(x, y, z, fx, fy, cx, cy)`
Projects a 3D point in metres back to a 2D image pixel using the pinhole camera model. Returns `(u, v)`, or `None` if `z <= 0`.

### `load_model(weights)`
Loads a YOLO model from a weights file. Downloads automatically if not present locally. Defaults to `yolov8x.pt`.

### `detect(model, left_rgb, classes=None)`
Runs YOLO on one RGB frame and returns the centre pixel `(cx, cy)` of the highest-confidence detection, or `None` if nothing was found. Defaults to COCO class 32 (sports ball). Pass a different `classes` list to detect other object types.

### `BallKalmanFilter`
Constant-velocity Kalman filter operating in 3D metres. State vector: `[x, y, z, vx, vy, vz]`.

- `init(x, y, z)` — seeds the filter with the first observed position, velocity initialised to zero.
- `predict()` — advances the state by one frame (`dt = 1/30 s`). Called every frame before the YOLO result is known.
- `correct(x, y, z)` — fuses a new 3D measurement into the state. Called only on frames where YOLO detects the ball with valid depth.
- `predict_ahead(horizon)` — extrapolates the current state forward by `horizon` seconds without modifying the filter. Used for future position prediction.

---

## main.py

Runs the full detection, tracking, and prediction loop over a single SVO2 file and writes an annotated output video.

**What it does, in order:**
1. Opens the SVO2 file, loads the YOLO model, and reads camera intrinsics.
2. Loops over every frame in the recording.
3. Calls `kf.predict()` to advance the Kalman filter state.
4. Runs YOLO detection on the RGB frame.
5. If the ball is detected with valid depth: corrects the Kalman filter with the 3D observation. Draws a **green** circle and `x, y, z` label.
6. If the ball is detected but depth is invalid: records the pixel position only, skips Kalman correction.
7. If YOLO misses (up to `MAX_MISS = 5` consecutive frames): projects the Kalman-predicted 3D position back to a pixel. Draws an **orange** circle and `[kf]` label.
8. Draws the **blue** trajectory trail of the last 10 positions.
9. Calls `kf.predict_ahead(PREDICTION_HORIZON)` and projects the result to draw a **red** hollow circle showing the predicted position `PREDICTION_HORIZON` seconds ahead.
10. Writes every frame to `output_detections.mp4`.

**Key constants (top of file):**
- `SVO_PATH` — input recording
- `PREDICTION_HORIZON` — how far ahead to predict in seconds (default `0.2`)
- `MAX_MISS` — consecutive missed frames before Kalman fill-in stops (default `5`)

**Run:**
```
PYTHON_COMMAND="python src/main.py" docker compose run --rm perception-x86
```

**Output:** `output_detections.mp4` — download via VSCode Remote SSH file explorer to view locally.
