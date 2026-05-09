# Evaluation Metrics

## Setup Assumptions

- Prediction horizon: 0.2 seconds
- Frame rate: 30 Hz
- Resolution: HD720p
- !!! Encoding format: TBD
- Timesteps per prediction: $T = 6$
- Output format: predicted 3D centroid positions $(x, y, z)$ in meters
- Tracking scenario: single moving object
- Evaluation mode: offline evaluation using recorded SVO2 sequences
- Reporting unit: per sequence, with summary statistics across all sequences

Ground truth trajectories are obtained from future observed object positions within the same recorded sequence.

Both pipelines are evaluated under identical conditions:
- same ZED 2i camera
- same SVO2 recordings
- same hardware platform
- same prediction horizon
- same tracking and prediction logic where possible

The evaluation compares:
- RGB-D-based perception pipeline
- XYZRGB point-cloud-based perception pipeline

---

# Primary Evaluation Metrics

## 1. Average Displacement Error (ADE)

**What it measures:** Mean Euclidean distance between predicted and ground truth positions across all predicted timesteps.

**Formula:**

$$
\text{ADE} = \frac{1}{T} \sum_{t=1}^{T} \left| \hat{p}_{t} - p_{t} \right|_2
$$

Where:

- $T = 6$ (number of predicted timesteps, i.e. 0.2 seconds at 30 Hz)
- $\hat{p}_{t} \in \mathbb{R}^3$ = predicted 3D object position at timestep $t$
- $p_{t} \in \mathbb{R}^3$ = ground truth 3D object position at timestep $t$

**Unit:** meters

**Reported as:** mean per sequence, overall mean across all sequences

Note: the subscript $_2$ specifies the Euclidean distance (L2 norm).

---

## 2. Final Displacement Error (FDE)

**What it measures:** Euclidean distance between predicted and ground truth positions at the final predicted timestep only.

**Formula:**

$$
\text{FDE} = \left| \hat{p}_{T} - p_{T} \right|_2
$$

Where:

- $T = 6$ (final prediction timestep)
- $\hat{p}_{T}$ = predicted object position at final timestep
- $p_{T}$ = ground truth object position at final timestep

**Unit:** meters

**Reported as:** mean per sequence, overall mean across all sequences

FDE measures prediction drift at the end of the prediction horizon.

---

## 3. Latency

**What it measures:** Time elapsed from receiving an input frame to outputting a prediction.

**Formula:**

$$
\text{Latency}_t = \tau_{\text{output},t} - \tau_{\text{input},t}
$$

Where:

- $t$ = frame index
- $\tau_{\text{input},t}$ = timestamp when frame $t$ was received
- $\tau_{\text{output},t}$ = timestamp when prediction for frame $t$ was output

**Unit:** milliseconds (ms)

**Reported as:** mean, 95th percentile and max across all frames

> Note: Even though evaluation is performed offline, latency is still relevant because large processing delays reduce the practical usefulness of short-term prediction systems.

---

# Perception and Tracking Quality Metrics

## 4. Position Stability (PS)

**What it measures:** Temporal stability of the estimated object position during tracking. Characterizes tracking jitter and perception noise.

**Formula:**

$$
\sigma_p = \sqrt{\frac{1}{N}\sum_{i=1}^{N}(p_i - \bar{p})^2}
$$

Where:

- $p_i$ = observed object position
- $\bar{p}$ = mean observed object position
- $N$ = number of tracked frames

**Unit:** meters

**Reported as:** standard deviation per axis and overall spatial variance

Lower values indicate more temporally stable tracking.

---

## 5. Track Completeness (TC)

**What it measures:** Percentage of frames in which the object has a valid track assigned. Characterizes tracking continuity and dropout frequency.

**Formula:**

$$
\text{TC} = \frac{\text{frames with valid track}}{\text{total visible frames}} \times 100
$$

Where:

- valid track = object successfully tracked
- visible frames = frames where the object is observable in the sequence

**Unit:** percentage (%)

**Reported as:** per sequence and overall mean across all sequences

Higher values indicate more stable tracking continuity.

---

# System Performance Metrics

## 6. Throughput (FPS)

**What it measures:** Number of frames processed per second.

**Formula:**

$$
\text{FPS} = \frac{N_{\text{frames}}}{t_{\text{processing}}}
$$

Where:

- $N_{\text{frames}}$ = total processed frames
- $t_{\text{processing}}$ = total processing time

**Unit:** frames per second

**Reported as:** mean FPS across each sequence

This metric characterizes computational efficiency of the pipeline.

---

## 7. Memory Usage

**What it measures:** Runtime memory consumption during pipeline execution.

**Unit:** MB or GB

**Reported as:**
- mean RAM usage
- peak RAM usage
- GPU memory usage when applicable

This metric is especially relevant when comparing RGB-D and dense point-cloud representations because point clouds typically require significantly more memory.

---

# Experimental Conditions

The comparison between RGB-D and XYZRGB point cloud representations is performed under identical experimental conditions.

Experimental scenarios may include:
- single moving object
- varying object speeds
- partial occlusion
- different lighting conditions
- different camera-object distances

The purpose of the evaluation is to compare:
- prediction accuracy
- tracking stability
- computational performance
- representation suitability for short-term prediction

while minimizing unrelated implementation differences between the two pipelines.

---

# Summary Table

| #   | Metric                     | Abbrev. | Stage            | Unit    | Reported As                |
| --- | -------------------------- | ------- | ---------------- | ------- | -------------------------- |
| 1   | Average Displacement Error | ADE     | Prediction       | meters  | mean per seq, overall mean |
| 2   | Final Displacement Error   | FDE     | Prediction       | meters  | mean per seq, overall mean |
| 3   | Latency                    | -       | System           | ms      | mean, p95, max             |
| 4   | Position Stability         | PS      | Tracking quality | meters  | std deviation, variance    |
| 5   | Track Completeness         | TC      | Tracking quality | %       | per seq, overall mean      |
| 6   | Throughput                 | FPS     | System           | FPS     | mean FPS                   |
| 7   | Memory Usage               | -       | System           | MB / GB | mean + peak                |