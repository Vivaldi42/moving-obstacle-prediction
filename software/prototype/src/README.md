# src

## pipeline.py

Reusable functions for the obstacle prediction pipeline. Nothing in here runs on its own.

### `open_svo(path)`
Opens a ZED SVO2 recording file for offline playback. Coordinates are set to metres. Returns an `sl.Camera` object ready to grab frames from.

### `grab_frame(cam, mat_rgb, mat_xyz, mat_conf)`
Advances to the next frame and returns three NumPy arrays:
- `left_rgb` - left camera image, shape `(H, W, 3)`, dtype `uint8`, RGB
- `xyz_map` - dense point cloud, shape `(H, W, 4)`, dtype `float32`, metres. Each pixel holds `(x, y, z, _)` where x=right, y=down, z=depth.
- `conf_map` - depth confidence per pixel, shape `(H, W)`, dtype `float32`, range 0-100.

Returns `None` at end of file.

### `load_model(weights)`
Loads a YOLO model from a weights file. Downloads automatically if not present locally. Defaults to `yolov8x.pt` (most accurate pretrained COCO model).

### `detect(model, left_rgb)`
Runs YOLO on one RGB frame, restricted to COCO class 32 (sports ball). Returns the centre pixel `(cx, cy)` of the highest-confidence detection, or `None` if no ball was found.

---

## main.py

Runs the full detection loop over a single SVO2 file and writes an annotated output video.

**What it does, in order:**
1. Opens the SVO2 file and loads the YOLO model.
2. Loops over every frame in the recording.
3. Detects the ball in each frame using YOLO.
4. Assigns a ball ID - the ID stays the same if the ball is missing for at most `MAX_GAP` frames, then increments when a new appearance is detected after a longer gap.
5. Reads the 3D position `(x, y, z)` in metres from the point cloud at the detected pixel.
6. Draws a green circle and a label showing `ID`, `x`, `y`, `z` on the frame.
7. Writes every frame (detected or not) to `output_detections.mp4` in the project root.

**Run:**
```
PYTHON_COMMAND="python src/main.py" docker compose run --rm perception-x86
```

**Output:** `output_detections.mp4` - download via VSCode Remote SSH file explorer to view locally.