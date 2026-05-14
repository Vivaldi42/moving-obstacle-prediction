# Evaluation Metrics

## Setup Assumptions

- Prediction horizon: 0.2 seconds
- Frame rate: 30 Hz
- Resolution: HD1080 (1920x1080)
- Encoding format: H265 LOSSLESS
- Timesteps per prediction: $T = 6$
- Output format: predicted 3D centroid positions $(x, y, z)$ in meters
- Tracking scenario: single moving object
- Evaluation mode: offline evaluation using recorded SVO2 sequences
- Reporting unit: per sequence, with summary statistics across all sequences
- Workstation specifications: 
	- AMD Ryzen 9 7950X (16 cores/32 threads)
	- 128 GB DDR5
	- 1 TB NVMe SSD
	- dual GeForce RTX 4090 (48 GB total VRAM)
	- Ubuntu 24.04 LTS
	- CUDA 13.0

Ground truth trajectories are obtained from future observed object positions within the same recorded sequence.

All pipeline configurations are evaluated under identical conditions: same ZED 2i camera, SVO2 recordings and workstation.

The evaluation compares different pipeline designs and algorithm choices across the detection, tracking and prediction stages, with the major focus lying on the prediction stage. The goal is to assess how design decisions at different stages affect overall system performance.

---

# Prediction Quality Metrics

## 1. Average Displacement Error (ADE)

**What it measures:** Mean Euclidean distance between predicted and ground truth positions across all predicted timesteps.

**Formula:**

$$
\text{ADE} = \frac{1}{T} \sum_{t=1}^{T} \left| \hat{p}_{t} - p_{t} \right|_2
$$

Where:
- $T = 6$ (number of predicted timesteps, i.e. 0.2 seconds at 30 Hz)
- $\hat{p}_{t} \in \mathbb{R}^3$ = predicted 3D object position $(x,y,z)$ at timestep $t$
- $p_{t} \in \mathbb{R}^3$ = ground truth 3D object position $(x,y,z)$ at timestep $t$

**Unit:** meters

**Reported as:** mean per sequence, overall mean across all sequences

Note: the subscript $_2$ denotes the L2 norm, which computes the straight-line Euclidean distance between two points in 3D space. For two positions $\hat{p}_t = (\hat{x}, \hat{y}, \hat{z})$ and $p_t = (x, y, z)$, this expands to $\sqrt{(\hat{x}-x)^2 + (\hat{y}-y)^2 + (\hat{z}-z)^2}$. This is the most natural distance measure for 3D spatial error and treats all three axes equally.

---

## 2. Final Displacement Error (FDE)

**What it measures:** Euclidean distance between predicted and ground truth positions at the final predicted timestep only.

**Formula:**

$$
\text{FDE} = \left| \hat{p}_{T} - p_{T} \right|_2
$$

Where:
- $T = 6$ (final prediction timestep)
- $\hat{p}_{T}$ = predicted object position $(x, y, z)$ at final timestep
- $p_{T}$ = ground truth object position $(x, y, z)$ at final timestep

**Unit:** meters

**Reported as:** mean per sequence, overall mean across all sequences

FDE measures prediction drift at the end of the prediction horizon.

---

# Tracking Quality Metrics

## 3. Track Completeness (TC)

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

## 4. Latency

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

Note: Even though evaluation is performed offline, latency is still relevant because large processing delays reduce the practical usefulness of short-term prediction systems.

---

## 5. Throughput

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

## 6. Memory Usage

**What it measures:** Runtime memory consumption during pipeline execution.

**Unit:** MB or GB

**Reported as:**
- mean RAM usage
- peak RAM usage
- GPU memory usage when applicable

---

# Experimental Conditions

All pipeline configurations are evaluated under identical experimental conditions.

Experimental scenarios include:
- single moving object
- varying object speeds
- occlusion

The purpose of the evaluation is to compare different pipeline designs across: prediction accuracy, tracking stability and computational performance while minimizing unrelated implementation differences between configurations.

---

# Summary Table

The major focus of the project is evaluating ADE and FDE.

| #     | Metric                         | Abbrev. | Measures               | Unit    | Reported As                    |
| ----- | ------------------------------ | ------- | ---------------------- | ------- | ------------------------------ |
| **1** | **Average Displacement Error** | **ADE** | **Prediction quality** | **m**   | **mean per seq, overall mean** |
| **2** | **Final Displacement Error**   | **FDE** | **Prediction quality** | **m**   | **mean per seq, overall mean** |
| 3     | Track Completeness (secondary) | TC      | Tracking quality       | %       | per seq, overall mean          |
| 4     | Latency                        | -       | System performance     | ms      | mean, p95, max                 |
| 5     | Throughput                     | FPS     | System performance     | FPS     | mean FPS                       |
| 6     | Memory Usage                   | -       | System performance     | MB / GB | mean and peak                  |

---

## Limitations

The following limitations apply to this evaluation framework and should be considered when interpreting results.

**Ground truth accuracy.** Ground truth trajectories are derived from future observed object positions within the same recorded sequence, extracted by the same perception pipeline under evaluation. This means ground truth is subject to the same depth noise and segmentation errors as the predictions being evaluated. Results therefore reflect error relative to a noisy reference, not absolute positional accuracy.

**Track Completeness definition.** The boundary between visible and non-visible frames is not formally defined. Edge cases such as partial occlusion or objects at the frame boundary are handled by judgment during annotation, which introduces inconsistency.

**No detection quality metric.** Detection failures are not directly measured. Missed detections manifest indirectly as lower TC scores but are not isolated or quantified independently.

**Statistical reliability.** The number of sequences per scenario is not fixed. Reported means across a small number of sequences should be interpreted with caution.