# SVO2 File Contents

## What is physically stored in the file

| Data | Format | Notes |
|------|--------|-------|
| Left camera frames | uint8 BGRA, H×W×4 | Raw stereo image, left eye |
| Right camera frames | uint8 BGRA, H×W×4 | Raw stereo image, right eye |
| Frame timestamps | int64 ms | Unix epoch, one per frame |
| Camera calibration | Header | Intrinsics (fx, fy, cx, cy, distortion) for both left and right; stereo baseline |
| Recording config | Header | Camera model, serial number, firmware version, resolution, FPS |
| Accelerometer | float, m/s² (x,y,z) | Stored only if the camera model has an IMU (ZED-M, ZED2, ZED2i, ZED X) |
| Gyroscope | float, deg/s (x,y,z) | Same condition as accelerometer |
| Barometer | float, hPa | Stored only if the camera model has a barometer (ZED2, ZED2i, ZED X) |
| Magnetometer | float, μT (x,y,z) | Stored only if the camera model has a magnetometer (ZED2i, ZED X) |

---

## What is computed by the ZED SDK (requires ZED SDK)

These are not stored — they are derived at runtime from the left + right stereo images.

| Data | How |
|------|-----|
| Depth map | ZED's proprietary stereo matching (NEURAL / ULTRA / QUALITY / PERFORMANCE modes) |
| Disparity map | By-product of stereo matching |
| Confidence map | Per-pixel reliability score from the stereo matcher |
| 3-D point cloud (XYZ / XYZRGBA) | Depth map + camera intrinsics → back-projected to 3D |
| Rectified left / right images | Lens distortion removed using calibration; required before stereo matching |
| Grayscale left / right | Colour-space conversion from the stored BGRA frames |

---

## What can be computed without the ZED SDK

These require only the raw stereo images and calibration parameters, which are extractable from the SVO2 file.

| Data | Tool | Notes |
|------|------|-------|
| Rectified images | OpenCV `initUndistortRectifyMap` + `remap` | Use the calibration stored in the file header |
| Disparity map | OpenCV `StereoBM` or `StereoSGBM` | Quality lower than ZED SDK's neural matcher |
| Depth map | Disparity × baseline × fx / disparity | Basic stereo geometry; no proprietary models |
| 3-D point cloud | `cv2.reprojectImageTo3D` | From the disparity + Q matrix |
| Grayscale frames | `cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)` | Trivial colour conversion |
| IMU dead-reckoning | Numerical integration of accelerometer + gyroscope | Drift accumulates quickly without fusion |
