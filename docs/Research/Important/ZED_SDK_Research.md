# ZED SDK Research

# Depth Shading

**Overview:**  
Depth shading is a visualization technique where depth data is converted into a grayscale (or colored) image to represent distance from the camera.

**Core idea:**  
A depth camera (like the ZED) measures distance per pixel. Depth shading maps these distances to intensity values: typically, closer objects appear brighter and farther objects darker (or vice versa, depending on settings). This is not new data, only a visual encoding of the depth map. It helps humans interpret 3D structure quickly without processing raw numerical depth values. Internally, the underlying data remains metric depth (e.g., meters), but shading compresses it into displayable ranges.

**Input:**
- Depth map (per-pixel distance values from ZED)

**Output:**
- 2D image where pixel intensity or color encodes depth

**Depends on:**
- Depth sensing (stereo matching in ZED)
- Normalization/scaling (min-max depth range)
- Colormap (grayscale, heatmap, etc.)

**Used in:**
- Debugging perception pipelines
- Visual inspection of scene geometry
- Previews in tools like ZED Depth Viewer

**Important distinction (often misunderstood):**
- Depth map = actual numeric data (used by algorithms)
- Depth shading = visualization of that data (for humans)

**Relevance to your project:**  
Depth shading is only a visualization layer. Your pipeline (detection, tracking, prediction) should operate on the raw depth or derived representations (e.g., point clouds), not on the shaded image.

---

# IMU Orientation

**Overview:**  
IMU orientation is the estimated 3D rotation (pose) of the camera/device in space, computed from inertial sensor data.

**Core idea:**  
An IMU (Inertial Measurement Unit) contains accelerometers and gyroscopes (sometimes magnetometers). The gyroscope measures angular velocity, and the accelerometer provides a gravity reference. By integrating angular velocity over time and correcting drift using gravity (and optionally magnetometer), the system estimates orientation. This orientation is typically represented as a quaternion or rotation matrix to avoid issues like gimbal lock. In the ZED system, IMU data is fused with visual tracking (visual-inertial odometry) to improve robustness and stability.

**Input:**

- Gyroscope data (angular velocity)
- Accelerometer data (linear acceleration, gravity vector)
- (Optional) Magnetometer data

**Output:**

- Orientation of the camera (rotation in 3D space)
    - Quaternion (most common)
    - Rotation matrix
    - Euler angles (roll, pitch, yaw)

**Depends on:**

- Sensor fusion algorithm (e.g., Kalman filter, complementary filter)
- Calibration of IMU
- Drift correction mechanisms
- Synchronization with camera frames

**Used in:**

- Camera pose estimation (SLAM, odometry)
- Stabilizing tracking in low-visual conditions
- Robotics navigation and control

**Relation to ZED / your pipeline:**

- ZED uses IMU + vision fusion → more stable tracking than vision-only
- Helps maintain consistent object tracking when visual features are weak
- Provides orientation component of the system “state” (position + rotation)
- Critical for transforming observations into a consistent world frame (needed for prediction)

**Key limitation:**

- IMU alone drifts over time (integration error)
- Reliable only when fused with vision (which ZED does internally)

---

# Depth Mode

**Overview:**  
Depth mode defines the algorithm and configuration used by the ZED camera to compute depth from stereo images, trading off accuracy, range, and computational cost.

**Core idea:**  
The ZED computes depth via stereo matching between its two cameras. Depth mode selects how this matching is performed internally (e.g., resolution, filtering, neural vs classical methods). Higher-quality modes use more complex algorithms (sometimes AI-based) to improve accuracy, especially in low-texture or noisy regions, but require more compute and increase latency. Simpler modes run faster but produce noisier or less complete depth maps. The choice of mode directly affects downstream tasks such as detection, tracking, and prediction, since all rely on the quality and stability of depth data.

**Input:**

- Stereo RGB images (left and right camera frames)

**Output:**

- Depth map (per-pixel distance)
- (Optionally derived) point cloud

**Depends on:**

- Stereo matching algorithm (classical vs AI-based)
- Resolution and internal scaling
- Post-processing (filtering, smoothing, hole filling)
- GPU compute availability (CUDA on NVIDIA hardware)

**Used in:**

- 3D perception pipelines
- Robotics navigation and obstacle avoidance
- Scene reconstruction and mapping

---

**Typical ZED depth modes (simplified):**

- **PERFORMANCE** - fastest, lowest accuracy
- **BALANCED** - trade-off between speed and quality
- **QUALITY** - higher accuracy, more compute
- **ULTRA** - highest accuracy, slower
- **NEURAL / AI-based** - best in challenging scenes, highest compute cost

(Note: exact availability depends on SDK version and hardware)

# Confidence

In the ZED desktop app, the “confidence” slider is effectively a **filter threshold**, not a probability. Setting it to 100% means **only the most reliable depth pixels are shown**, so the image looks cleaner.