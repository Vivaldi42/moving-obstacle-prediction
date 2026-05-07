# Evaluation Metrics

## Setup Assumptions

- Prediction horizon: 1 second
- Frame rate: 30 Hz
- Resolution: HD720p
- Encoding format: H264 Lossy
- Timesteps per prediction: $T = 30$
- Output format: 3D positions $(x, y, z)$ in meters
- Reporting unit: per sequence, with summary statistics across all sequences

---

# Primary Evaluation Metrics

## 1. Average Displacement Error (ADE)

**What it measures:** Mean Euclidean distance between predicted and ground truth positions across all objects and all predicted timesteps.

**Formula:**

$$\text{ADE} = \frac{1}{N \cdot T} \sum_{n=1}^{N} \sum_{t=1}^{T} \left| \hat{p}_{n,t} - p_{n,t} \right|_2$$

Where:

- $N$ = number of tracked objects in the sequence
- $T$ = 30 (number of predicted timesteps, i.e. 1 second at 30 Hz)
- $\hat{p}_{n,t} \in \mathbb{R}^3$ = predicted 3D position of object $n$ at timestep $t$
- $p_{n,t} \in \mathbb{R}^3$ = ground truth 3D position of object $n$ at timestep $t$

**Unit:** meters

**Reported as:** mean per sequence, overall mean across all sequences

Note: the subscript $_2$ at the end of the formula specifies the norm being used in this case the Euclidean distance (L2 norm).

---

## 2. Final Displacement Error (FDE)

**What it measures:** Euclidean distance between predicted and ground truth positions at the final predicted timestep only (t = 30, i.e. 1 second ahead).

**Formula:**

$$\text{FDE} = \frac{1}{N} \sum_{n=1}^{N} \left| \hat{p}_{n,T} - p_{n,T} \right|_2$$

Where:

- $N$ = number of tracked objects in the sequence
- $T$ = 30 (final timestep)
- $\hat{p}_{n,T}$ = predicted position of object $n$ at final timestep
- $p_{n,T}$ = ground truth position of object $n$ at final timestep

**Unit:** meters

**Reported as:** mean per sequence, overall mean across all sequences

---

## 3. Latency

**What it measures:** Time elapsed from receiving an input frame to outputting a prediction. Determines real-time feasibility.

**Formula:**

$$\text{Latency}_t = \tau_{\text{output,t}} - \tau_{\text{input,t}}$$
Where:

- $t$ = frame index
- $\tau_{\text{input},t}$ = timestamp when frame $t$ was received
- $\tau_{\text{output},t}$​ = timestamp when prediction for frame $t$ was output

**Unit:** milliseconds (ms)

**Reported as:** mean, 95th percentile, and max across all frames

> Note: The 95th percentile is more informative than the mean for real-time feasibility assessment. A system with low mean latency but high peak latency is unreliable for real-time robotics use.
>
 
---

# Input Tracking Quality Metrics

## 4. ID Switches (ID\_SW)

**What it measures:** Number of times a tracked object is assigned a new identity between consecutive frames, despite being the same physical object. Caused by tracking failures in the ZED SDK. Reported to characterize tracking input quality, not as a primary evaluation target.

**Formula:**

$$\text{ID\_SW}(\text{seq}) = \#\left\{ t : \text{ID}_{n,t} \neq \text{ID}_{n,t-1} \right\}$$

Where:

- $\#\{\cdot\}$ denotes the count of frames where an identity change occurred
- $t$ = frame index in the sequence 
- $\text{ID}_{n,t}$ = identity assigned to object $n$ at frame $t$

**Unit:** count (integer)

**Reported as:** per sequence, plus mean and max across all sequences

---
## 5. Track Completeness (TC)

**What it measures:** For a given object, the percentage of frames in which it has a valid track assigned. Characterizes gaps or dropouts in tracking input. Reported to characterize tracking input quality, not as a primary evaluation target.

**Formula:**

Per object:

$$\text{TC}(n) = \frac{\text{frames where object } n \text{ has valid track}}{\text{total frames in which object } n \text{ is visible}} \times 100$$

Per sequence (aggregated over all objects $N$):

$$\text{TC}(\text{seq}) = \frac{1}{N} \sum_{n=1}^{N} \text{TC}(n)$$

**Unit:** percentage (%)

**Reported as:** per sequence, plus mean across all sequences

---


---

## Summary Table

| #   | Metric                     | Abbrev. | Stage                    | Unit   | Reported As                 |
| --- | -------------------------- | ------- | ------------------------ | ------ | --------------------------- |
| 1   | Average Displacement Error | ADE     | Prediction               | meters | mean per seq, overall mean  |
| 2   | Final Displacement Error   | FDE     | Prediction               | meters | mean per seq, overall mean  |
| 3   | Latency                    | -       | System                   | ms     | mean, p95, max              |
| 4   | ID Switches                | ID_SW   | Tracking (input quality) | count  | per seq, mean + max summary |
| 5   | Track Completeness         | TC      | Tracking (input quality) | %      | per seq, mean summary       |

