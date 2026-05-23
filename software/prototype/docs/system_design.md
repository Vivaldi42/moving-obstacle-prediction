# System design

## Overview

The prototype processes a pre-recorded ZED stereo camera video to detect a sports ball, track it in 3D space, and predict its position 0.2 seconds ahead. The result is an annotated video with the ball's trail, current position, and predicted future position drawn on each frame.

```
SVO2 file
    |
    v
[READ] grab_frame()
    - left RGB image (1920x1080)
    - XYZ map (same resolution, metres)
    |
    v
[DETECT] YOLO
    - runs on left RGB only
    - returns centre pixel (cx, cy) of highest-confidence sports ball box
    - or: miss -> fall back to Kalman prediction
    |
    v
[LOCATE] resolve_xyz()
    - looks up xyz_map[cy, cx] -> (x, y, z) in metres (camera space)
    - depth is surface nearest to camera, not geometric centre of object
    - patch fallback if centre pixel is invalid (stereo occlusion at edges)
    |
    v
[PREDICT] BallKalmanFilter
    - smooths noisy raw (x, y, z) measurements across frames
    - estimates velocity from position history
    - extrapolates position 0.2 s ahead
    |
    v
[OUTPUT] annotated frame -> MP4
    - blue trail: last 10 pixel positions
    - green circle: current detection (depth valid)
    - orange circle: Kalman coast (no detection, predicted position used)
    - red circle + line: predicted position 0.2 s ahead
```

---

## Input

**Format:** SVO2 (Stereolabs proprietary format)

The SVO2 file is opened in non-real-time playback mode, so frames are processed as fast as compute allows rather than at wall-clock speed. Coordinate units are set to metres at open time so all downstream code works in a single consistent unit.

See [svo2_format.md](svo2_format.md) for a full breakdown of what is stored vs. computed at playback.

---

## Step 1 - read

Each frame yields two arrays from the ZED SDK:

| Array | Shape | Content |
|---|---|---|
| `left_rgb` | `(H, W, 3)` uint8 | Color image from the left lens |
| `xyz_map` | `(H, W, 4)` float32 | Per-pixel `(x, y, z, _)` in metres, camera space |

The XYZ map is pixel-aligned with the RGB image - index `(cy, cx)` in both arrays refers to the same physical point in the scene.

---

## Step 2 - detect

YOLO (YOLOv8x) runs on the left RGB image and returns bounding boxes filtered to class 32 (sports ball) with confidence >= 0.25. The centre pixel of the highest-confidence box is taken as the detection:

```
cx = (x1 + x2) / 2
cy = (y1 + y2) / 2
```

YOLO operates entirely in 2D image space and has no knowledge of depth or 3D position.

---

## Step 3 - locate

The centre pixel `(cx, cy)` is used to index into the XYZ map:

```
xyz_map[cy, cx] -> (x, y, z)
```

**What this point represents:** stereo depth measures the first visible surface from the camera's perspective, so the returned point is on the front surface of the object, not its geometric centre. For a small ball at tracking distances, the offset is a few centimetres and is systematic (consistent direction, consistent magnitude), so it does not distort the trajectory shape. This applies to any object type, not just balls.

**Patch fallback:** stereo matching often fails at object edges (occlusion between the two lenses). If the centre pixel returns NaN/inf, a 9x9 patch around it is sampled and the median of valid points is returned. Median is used rather than mean because depth noise at edges is non-Gaussian and contains outliers.

If no valid depth is found in the patch, the frame is treated as a miss.

---

## Step 4 - predict

A constant-velocity Kalman filter operates in 3D metres with state `[x, y, z, vx, vy, vz]` and direct position measurements `[x, y, z]`.

**Smoothing:** raw depth measurements contain small random errors per frame. The filter blends each new measurement with prior state to produce a cleaner position estimate.

**Velocity estimation:** by tracking position across frames the filter maintains a velocity estimate, which enables prediction without any explicit velocity measurement.

**Miss handling:** if YOLO returns no detection for up to `MAX_MISS = 5` consecutive frames, the filter's last predicted position is used in place of a measurement. This keeps tracking alive through brief occlusions or detection failures.

**Forward prediction:** position 0.2 s ahead is computed as linear extrapolation from current state:

```
x_future = x + vx * horizon
```

This is equivalent to running the Kalman predict step forward N times (since the process model is linear) but avoids accumulating covariance from repeated predict calls that would corrupt the filter's internal state.

**Noise parameters:**

| Parameter | Value | Rationale |
|---|---|---|
| Position process noise | `1e-4` | Ball position changes smoothly between frames |
| Velocity process noise | `1e-2` | Velocity is allowed to drift more freely |
| Measurement noise | `1e-3` | ZED depth noise is ~1-2 cm at short range |

---

## Output

Each annotated frame is written to an MP4 at 30 FPS (1920x1080). The four visual overlays and their meaning:

| Overlay | Colour | Meaning |
|---|---|---|
| Trail | Blue | Last 10 pixel positions (raw detections and coasted predictions) |
| Current position | Green | Detection confirmed with valid depth this frame |
| Coasted position | Orange | No detection - Kalman predicted position used |
| Future prediction | Red | Estimated position 0.2 s from now |
