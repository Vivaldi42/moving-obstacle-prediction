# Kalman Filter - Mathematical Notes

## 1. What the filter tracks

The filter maintains a **state vector** $\hat{x}$ - everything it knows about the ball at a given timestep:

$$
\hat{x} = \begin{bmatrix} x \\ y \\ z \\ v_x \\ v_y \\ v_z \end{bmatrix}
$$

Position $(x, y, z)$ is observed directly by the camera. Velocity $(v_x, v_y, v_z)$ is not measured - it is inferred over time from how position changes.

---

## 2. Transition Matrix - encoding the physics

The filter uses a constant-velocity model. Given the current state, the predicted next state is:

$$
x_\text{new} = x + v_x \cdot \Delta t, \quad
y_\text{new} = y + v_y \cdot \Delta t, \quad
z_\text{new} = z + v_z \cdot \Delta t
$$

$$
v_{x,\text{new}} = v_x, \quad v_{y,\text{new}} = v_y, \quad v_{z,\text{new}} = v_z
$$

Written as a single matrix multiplication $\hat{x}^- = F \hat{x}$, where the **transition matrix** $F$ is:

$$
F = \begin{bmatrix}
1 & 0 & 0 & \Delta t & 0 & 0 \\
0 & 1 & 0 & 0 & \Delta t & 0 \\
0 & 0 & 1 & 0 & 0 & \Delta t \\
0 & 0 & 0 & 1 & 0 & 0 \\
0 & 0 & 0 & 0 & 1 & 0 \\
0 & 0 & 0 & 0 & 0 & 1
\end{bmatrix}
$$

The superscript $^-$ on $\hat{x}^-$ means "predicted, before correction with a measurement".

---

## 3. Measurement Matrix - what the camera sees

The camera returns only position - a 3-vector $z = [x, y, z]^\top$. The state has 6 values. The **measurement matrix** $H$ extracts the observable part of the state:

$$
H = \begin{bmatrix}
1 & 0 & 0 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 & 0
\end{bmatrix}
$$

So $H \hat{x}$ projects the 6-value state down to a 3-value prediction of what the camera should see:

$$
H \hat{x} = \begin{bmatrix} x \\ y \\ z \end{bmatrix}
$$

This is needed so the filter can compare its internal prediction to the camera reading - they must be in the same space.

---

## 4. Process Noise - how wrong is the physics model?

The constant-velocity model is an approximation. The ball may bounce, spin, or accelerate. This unmodelled behaviour is captured by the **process noise covariance** $Q$:

$$
Q = \begin{bmatrix}
\sigma^2_x & & & & & \\
& \sigma^2_y & & & & \\
& & \sigma^2_z & & & \\
& & & \sigma^2_{v_x} & & \\
& & & & \sigma^2_{v_y} & \\
& & & & & \sigma^2_{v_z}
\end{bmatrix}
$$

In this implementation, the diagonal values are:

$$
Q = \text{diag}(0.0001,\ 0.0001,\ 0.0001,\ q_v,\ q_v,\ q_v)
$$

where $q_v = 0.01$ by default. Velocity gets 100x higher noise than position because the constant-velocity assumption breaks down at velocity changes (bounces, acceleration).

**Effect:** larger $Q$ → filter trusts its own physics prediction less → relies more on the camera.

---

## 5. Measurement Noise - how wrong is the camera?

The ZED camera has per-axis noise characterised by a static experiment. This is captured by the **measurement noise covariance** $R$:

$$
R = \begin{bmatrix}
\sigma^2_{m_x} & & \\
& \sigma^2_{m_y} & \\
& & \sigma^2_{m_z}
\end{bmatrix}
= \text{diag}(0.001,\ 0.001,\ 0.001)
$$

Each diagonal entry is a variance in $\text{m}^2$, giving a standard deviation of ~1 cm per axis.

**Effect:** larger $R$ → filter trusts the camera less → relies more on the physics prediction.

---

## 6. The Predict-Correct Loop

Every frame runs two steps.

### Predict

Step the physics model forward - no camera involved:

$$
\hat{x}^-_k = F \hat{x}_{k-1}
$$

### Correct

The camera gives measurement $z_k$. First compute the **innovation** - the gap between what was predicted and what was observed:

$$
\tilde{y}_k = z_k - H \hat{x}^-_k
$$

Then blend the prediction with the measurement using the **Kalman gain** $K$:

$$
\hat{x}_k = \hat{x}^-_k + K \tilde{y}_k
$$

### Data flow

$$
\hat{x}_{k-1}
\xrightarrow{\ F \ }
\hat{x}^-_k
\xrightarrow{\ +K\tilde{y}_k \ }
\hat{x}_k
$$

$$
z_k \ \longrightarrow \ \tilde{y}_k = z_k - H\hat{x}^-_k \ \longrightarrow \ K\tilde{y}_k
$$

$Q$ and $R$ determine how $K$ is computed - covered in the next section.

---

## 7. Tuning

| Parameter | Default | Increase effect | Decrease effect |
|-----------|---------|-----------------|-----------------|
| $q_v$ (diagonal of $Q$) | $0.01$ | faster response, more jitter | smoother, slower to react |
| $\sigma^2_{m}$ (diagonal of $R$) | $0.001$ | smoother, relies more on physics | more responsive to camera |

$$
\text{Low } Q, \text{ High } R \quad \Rightarrow \quad \text{trust physics, smooth but slow}
$$

$$
\text{High } Q, \text{ Low } R \quad \Rightarrow \quad \text{trust camera, responsive but jittery}
$$

---

*Not yet documented: error covariance $P$, Kalman gain $K$ derivation, filter initialisation, $\texttt{predict\_ahead()}$.*
