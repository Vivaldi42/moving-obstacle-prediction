# SVO2 File Format

SVO2 is Stereolabs' proprietary recording format for ZED stereo cameras. A single `.svo2` file captures stereo images, embedded calibration, per-frame timestamps, and IMU sensor samples at their native sensor frequency.

---

## What You Can Access as a Developer

### Directly from the Recording (stored data)

#### Images - `retrieve_image(mat, view)`

Retrieved per frame after calling `grab()`. Available views:

- `VIEW.LEFT` - left lens image, primary RGB feed
- `VIEW.RIGHT` - right lens image
- `VIEW.SIDE_BY_SIDE` - both images side by side

Returns BGRA format (8-bit, 4 channels).

#### Timestamps - `get_timestamp(sl.TIME_REFERENCE.IMAGE)`

Nanosecond-precision timestamp per frame, marking when the image was captured.

```python
ts = cam.get_timestamp(sl.TIME_REFERENCE.IMAGE)
ts.get_milliseconds()
```

#### IMU and Sensor Data - `get_sensors_data()`

ZED 2 and newer cameras have a built-in IMU. In SVO2, sensor data is recorded at the sensor's native frequency (higher than the image frame rate), not just once per image frame. Each sample contains:

- **Accelerometer** - linear acceleration in m/s² along X, Y, Z
- **Gyroscope** - angular velocity in rad/s around X, Y, Z
- **Magnetometer** - heading reference
- **Barometer and temperature sensors** - environmental readings

```python
sensors = sl.SensorsData()
cam.get_sensors_data(sensors, sl.TIME_REFERENCE.IMAGE)
imu = sensors.get_imu_data()
imu.get_linear_acceleration()
imu.get_angular_velocity()
```

#### Calibration - `get_camera_information().calibration_parameters`

Returns intrinsics for both lenses (fx, fy, cx, cy, distortion coefficients) and the stereo baseline (physical distance between the lenses). Available after `open()`, before any `grab()` call.

#### SVO Navigation

- `get_svo_position()` - current frame index
- `set_svo_position(n)` - seek to arbitrary frame
- `get_svo_number_of_frames()` - total frame count

---

### Computed at Playback (not stored, derived from stereo images)

All of the following are computed by the ZED SDK on each `grab()` call via stereo matching on the left and right images. Retrieved via `retrieve_measure(mat, measure)`.

| Measure | Description | Output |
|---|---|---|
| `MEASURE.DEPTH` | Scalar Z distance per pixel | 32-bit float per pixel, in configured units |
| `MEASURE.XYZ` | 3D position per pixel, no color | `(x, y, z, _)` float32, in metres |
| `MEASURE.XYZRGBA` | 3D position + packed RGBA color per pixel | `(x, y, z, color)` float32 |
| `MEASURE.NORMALS` | Surface normal vectors per pixel | `(x, y, z, _)` float32 |
| `MEASURE.CONFIDENCE` | Per-pixel reliability score for depth | float32 |

Accessing a specific pixel:
```python
point3D = point_cloud.get_value(i, j)
x, y, z, color = point3D
```

**Notes:**
- Depth units are set via `InitParameters.coordinate_units` (default: millimetres for `MEASURE.DEPTH`, metres for `MEASURE.XYZ`)
- You can retrieve at reduced resolution by passing width/height to `retrieve_measure()`
- Data can be retrieved in CPU (default) or GPU memory: `retrieve_measure(mat, measure, sl.MEM.GPU)`
- `VIEW.DEPTH` via `retrieve_image()` returns a normalized 8-bit grayscale depth image for display only - do not use it for computation

---

## The Core Loop

Every pipeline iteration follows the same pattern:

```python
zed.grab()                                        # advance one frame, trigger stereo matching
zed.retrieve_image(mat, sl.VIEW.LEFT)             # get RGB image
zed.retrieve_measure(mat, sl.MEASURE.XYZ)         # get 3D point cloud
zed.get_sensors_data(sensors, ...)                # get IMU data
zed.get_timestamp(sl.TIME_REFERENCE.IMAGE)        # get frame timestamp
```

All `retrieve_*` calls after `grab()` are cheap lookups into already-computed buffers. You can call as many as needed per frame.

---

## How This Prototype Uses the API

| Pipeline step | API call |
|---|---|
| `open_svo()` | `zed.open(init_params)` with `set_from_svo_file()` |
| `get_intrinsics()` | `get_camera_information().calibration_parameters` |
| `grab_frame()` | `zed.grab()` then `retrieve_image(LEFT)` + `retrieve_measure(XYZ)` |
| `detect()` | YOLO runs on the left RGB image |
| `resolve_xyz()` | `point_cloud.get_value(i, j)` at the detected pixel |
| Kalman filter | Consumes the 3D `(x, y, z)` position in metres |

The right image, IMU data, normals and confidence map are available but unused by this prototype.