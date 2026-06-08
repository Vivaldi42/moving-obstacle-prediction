# Kalman Filter - Explained from Scratch

---

## What is a Kalman Filter?

You are trying to track a moving ball. You have two sources of information:

1. **Your model** - "I know where the ball was and how fast it was moving, so I can predict where it is now."
2. **Your sensor** - "The camera measured the ball at this position, but the measurement is noisy."

Both are imperfect. The Kalman filter is an algorithm that **optimally combines these two noisy sources** every single frame to get the best possible estimate of where the ball is.

---

## Notation

| Symbol | Meaning |
|--------|---------|
| $\mathbf{s}$ | State vector - everything we track |
| $P$ | Uncertainty matrix - how confident we are |
| $F$ | Transition matrix - motion model |
| $H$ | Measurement matrix - what the sensor can see |
| $Q$ | Process noise - how much we distrust the model |
| $R$ | Measurement noise - how much we distrust the sensor |
| $K$ | Kalman gain - how much to trust sensor vs model |
| $\mathbf{z}$ | Measurement from the sensor |
| $\mathbf{y}$ | Residual - how wrong the prediction was |
| $\hat{\mathbf{s}}$ | Predicted state (before update) |
| $P^{-}$ | Predicted uncertainty (before update) |
| $\top$ | Transpose - flipping rows and columns of a matrix |
| $^{-1}$ | Matrix inverse - the matrix equivalent of dividing |

### What is transpose $\top$?

Flipping a matrix so rows become columns:

$$\mathbf{v} = \begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix} \quad \Rightarrow \quad \mathbf{v}^\top = \begin{bmatrix} 1 & 2 & 3 \end{bmatrix}$$

---

## State Vector

Everything the filter tracks is packed into one vector called the **state**:

$$\mathbf{s} = \begin{bmatrix} x \\ y \\ z \\ v_x \\ v_y \\ v_z \end{bmatrix}$$

- $(x, y, z)$ - position of the ball in 3D space (meters)
- $(v_x, v_y, v_z)$ - velocity of the ball in each direction (meters per second)

The filter estimates this vector at every frame.

---

## Uncertainty Matrix $P$

The filter does not just track the state - it also tracks **how uncertain it is** about the state. This is stored in $P$, a $6 \times 6$ matrix.

- Diagonal entries = how uncertain we are about each state variable
- Off-diagonal entries = whether errors in one variable are correlated with another

**Big $P$ = uncertain. Small $P$ = confident.**

---

## Step 0 - Initialization (First Detection)

On the very first detection, the camera gives us a position. We set:

$$\mathbf{s}_0 = \begin{bmatrix} x_{\text{measured}} \\ y_{\text{measured}} \\ z_{\text{measured}} \\ 0 \\ 0 \\ 0 \end{bmatrix}$$

Velocity is set to zero because we have no information yet. Initial uncertainty:

$$P_0 = \begin{bmatrix} 1 & 0 & 0 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 & 0 & 0 \\ 0 & 0 & 1 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 0 & 0 & 1 \end{bmatrix}$$

This is the identity matrix - moderate uncertainty about everything.

---

## The Loop - Two Steps Per Frame

### Step 1 - Predict

Before looking at the camera, we ask: **where do we think the ball is now, based on where it was last frame?**

#### Transition Matrix $F$

The constant-velocity model says: new position = old position + velocity * time. Written as a matrix:

$$F = \begin{bmatrix} 1 & 0 & 0 & \frac{1}{30} & 0 & 0 \\ 0 & 1 & 0 & 0 & \frac{1}{30} & 0 \\ 0 & 0 & 1 & 0 & 0 & \frac{1}{30} \\ 0 & 0 & 0 & 1 & 0 & 0 \\ 0 & 0 & 0 & 0 & 1 & 0 \\ 0 & 0 & 0 & 0 & 0 & 1 \end{bmatrix}, \quad \Delta t = \frac{1}{30} \text{ s}$$

#### Predicted State

$$\hat{\mathbf{s}}_t = F \cdot \mathbf{s}_{t-1} = \begin{bmatrix} x_{t-1} + v_{x,t-1} \cdot \frac{1}{30} \\ y_{t-1} + v_{y,t-1} \cdot \frac{1}{30} \\ z_{t-1} + v_{z,t-1} \cdot \frac{1}{30} \\ v_{x,t-1} \\ v_{y,t-1} \\ v_{z,t-1} \end{bmatrix}$$

Position moves forward by velocity * time. Velocity stays the same.

#### Process Noise $Q$

The model is not perfect - the ball might bounce or change direction. $Q$ represents how much we distrust our own prediction:

$$Q = \begin{bmatrix} 0.0001 & 0 & 0 & 0 & 0 & 0 \\ 0 & 0.0001 & 0 & 0 & 0 & 0 \\ 0 & 0 & 0.0001 & 0 & 0 & 0 \\ 0 & 0 & 0 & 0.01 & 0 & 0 \\ 0 & 0 & 0 & 0 & 0.01 & 0 \\ 0 & 0 & 0 & 0 & 0 & 0.01 \end{bmatrix}$$

Small values on position rows ($0.0001$) - position changes predictably. Larger values on velocity rows ($0.01$) - velocity can change unexpectedly.

#### Predicted Uncertainty

Because time has passed and things can change, we become slightly less confident:

$$P_t^{-} = F \cdot P_{t-1} \cdot F^\top + Q$$

The $-$ superscript means "before looking at the camera this frame."

---

### Step 2 - Update

Now the camera gives us a new measurement. We use it to correct our prediction.

#### Measurement Vector $\mathbf{z}$

$$\mathbf{z}_t = \begin{bmatrix} x_{\text{measured}} \\ y_{\text{measured}} \\ z_{\text{measured}} \end{bmatrix}$$

#### Measurement Matrix $H$

The camera only measures position, not velocity. $H$ extracts the position part from the state:

$$H = \begin{bmatrix} 1 & 0 & 0 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 & 0 & 0 \\ 0 & 0 & 1 & 0 & 0 & 0 \end{bmatrix}$$

So $H \cdot \hat{\mathbf{s}}_t$ gives:

$$H \cdot \hat{\mathbf{s}}_t = \begin{bmatrix} 1 & 0 & 0 & 0 & 0 & 0 \\ 0 & 1 & 0 & 0 & 0 & 0 \\ 0 & 0 & 1 & 0 & 0 & 0 \end{bmatrix} \cdot \begin{bmatrix} \hat{x}_t \\ \hat{y}_t \\ \hat{z}_t \\ \hat{v}_{x,t} \\ \hat{v}_{y,t} \\ \hat{v}_{z,t} \end{bmatrix} = \begin{bmatrix} \hat{x}_t \\ \hat{y}_t \\ \hat{z}_t \end{bmatrix}$$

#### Residual $\mathbf{y}$ - How Wrong Was the Prediction?

$$\mathbf{y}_t = \mathbf{z}_t - H \cdot \hat{\mathbf{s}}_t = \begin{bmatrix} x_{\text{measured}} - \hat{x}_t \\ y_{\text{measured}} - \hat{y}_t \\ z_{\text{measured}} - \hat{z}_t \end{bmatrix}$$

If the model was perfect, $\mathbf{y}_t = \mathbf{0}$.

#### Measurement Noise $R$

The sensor is also noisy. $R$ represents how much we distrust the camera:

$$R = \begin{bmatrix} 0.001 & 0 & 0 \\ 0 & 0.001 & 0 \\ 0 & 0 & 0.001 \end{bmatrix}$$

This corresponds to roughly 3 cm standard deviation in each axis ($\sqrt{0.001} \approx 0.032$ m) - consistent with ZED camera depth accuracy at short range.

---

#### Kalman Gain $K$ - Step by Step

This is the core of the filter. $K$ decides how much to trust the sensor vs the model.

$$K = P_t^{-} \cdot H^\top \cdot \left( H \cdot P_t^{-} \cdot H^\top + R \right)^{-1}$$

We compute it in pieces:

**Piece 1 - $H \cdot P_t^{-}$**

$H$ is $3 \times 6$, $P_t^{-}$ is $6 \times 6$. Result is $3 \times 6$.

This extracts only the rows of $P_t^{-}$ that relate to position - "which parts of our uncertainty are relevant to what the sensor can see?"

$$H \cdot P_t^{-} = \text{first 3 rows of } P_t^{-}$$

**Piece 2 - $H \cdot P_t^{-} \cdot H^\top$**

Take Piece 1 ($3 \times 6$) and multiply by $H^\top$ ($6 \times 3$). Result is $3 \times 3$.

This also extracts the relevant columns. Now we have only the uncertainty that relates to position - a $3 \times 3$ matrix:

$$H \cdot P_t^{-} \cdot H^\top = \begin{bmatrix} P_{xx} & P_{xy} & P_{xz} \\ P_{yx} & P_{yy} & P_{yz} \\ P_{zx} & P_{zy} & P_{zz} \end{bmatrix}$$

**Piece 3 - $H \cdot P_t^{-} \cdot H^\top + R$**

Add the sensor noise $R$ to Piece 2. Result is still $3 \times 3$:

$$H \cdot P_t^{-} \cdot H^\top + R = \begin{bmatrix} P_{xx} + 0.001 & P_{xy} & P_{xz} \\ P_{yx} & P_{yy} + 0.001 & P_{yz} \\ P_{zx} & P_{zy} & P_{zz} + 0.001 \end{bmatrix}$$

This is the **total uncertainty in measurement space** - combining prediction uncertainty and sensor noise.

**Piece 4 - $\left( H \cdot P_t^{-} \cdot H^\top + R \right)^{-1}$**

Invert the matrix from Piece 3. Call the result $S^{-1}$ where $S = H \cdot P_t^{-} \cdot H^\top + R$.

Large $S$ (high total uncertainty) gives small $S^{-1}$, which will make $K$ smaller - correct less aggressively.

**Piece 5 - $P_t^{-} \cdot H^\top$**

$P_t^{-}$ is $6 \times 6$, $H^\top$ is $6 \times 3$. Result is $6 \times 3$.

This is the first 3 columns of $P_t^{-}$ - how does the uncertainty of the full state (all 6 variables) relate to position uncertainty? This includes cross-terms like how uncertain $v_x$ is correlated with $x$:

$$P_t^{-} \cdot H^\top = \begin{bmatrix} P_{xx} & P_{xy} & P_{xz} \\ P_{yx} & P_{yy} & P_{yz} \\ P_{zx} & P_{zy} & P_{zz} \\ P_{v_x x} & P_{v_x y} & P_{v_x z} \\ P_{v_y x} & P_{v_y y} & P_{v_y z} \\ P_{v_z x} & P_{v_z y} & P_{v_z z} \end{bmatrix}$$

**Final - Multiply Pieces 5 and 4**

$$K = \underbrace{P_t^{-} \cdot H^\top}_{6 \times 3} \cdot \underbrace{\left( H \cdot P_t^{-} \cdot H^\top + R \right)^{-1}}_{3 \times 3} = \underbrace{K}_{6 \times 3}$$

$K$ is a $6 \times 3$ matrix. It answers: "for each meter of error in the measurement $(x, y, z)$, how much should each of the 6 state variables be corrected?"

**Intuition:**

$$K \approx \frac{\text{prediction uncertainty}}{\text{prediction uncertainty} + \text{sensor noise}}$$

- Prediction uncertain + sensor accurate = $K$ large = trust sensor, correct strongly
- Prediction confident + sensor noisy = $K$ small = trust model, correct weakly

---

#### State Update

$$\mathbf{s}_t = \hat{\mathbf{s}}_t + K \cdot \mathbf{y}_t$$

Expanded:

$$\begin{bmatrix} x_t \\ y_t \\ z_t \\ v_{x,t} \\ v_{y,t} \\ v_{z,t} \end{bmatrix} = \begin{bmatrix} \hat{x}_t \\ \hat{y}_t \\ \hat{z}_t \\ \hat{v}_{x,t} \\ \hat{v}_{y,t} \\ \hat{v}_{z,t} \end{bmatrix} + K \cdot \begin{bmatrix} x_{\text{measured}} - \hat{x}_t \\ y_{\text{measured}} - \hat{y}_t \\ z_{\text{measured}} - \hat{z}_t \end{bmatrix}$$

Note: **velocity also gets updated here**, even though we never measured it. This happens because $K$ has rows for velocity too - the filter infers velocity correction from position error.

#### Uncertainty Update

Because we just got new information, we become more confident:

$$P_t = \left( I - K \cdot H \right) \cdot P_t^{-}$$

Where $I$ is the $6 \times 6$ identity matrix. $(I - KH)$ shrinks $P$ - uncertainty decreases.

---

## Concrete Example - One Frame

Say last frame the ball was at $x = 1.0$ m, $v_x = 0.6$ m/s.

**Predict:**

$$\hat{x}_t = 1.0 + 0.6 \cdot \frac{1}{30} = 1.02 \text{ m}$$

**Camera measures:** $x_{\text{meas}} = 1.04$ m

**Residual:**

$$y = 1.04 - 1.02 = 0.02 \text{ m}$$

**Say $K = 0.8$** (trust the sensor more than the model):

$$x_t = 1.02 + 0.8 \cdot 0.02 = 1.036 \text{ m}$$

The final estimate $1.036$ m sits between prediction ($1.02$) and measurement ($1.04$), but closer to the measurement because $K$ was high.

---

## What Happens When the Ball is Not Detected?

If YOLO misses the ball (up to `MAX_MISS = 5` frames), there is no measurement. The filter skips the update step and only runs the predict step - it keeps estimating position from velocity alone. This is called **coasting.**

---

## Forward Prediction (the Red Circle)

After the filter runs, the code draws where the ball will be 0.2 seconds in the future. This is simple physics - no filter involved:

$$\hat{p}_{t+h} = \begin{bmatrix} x + v_x \cdot h \\ y + v_y \cdot h \\ z + v_z \cdot h \end{bmatrix}, \quad h = 0.2 \text{ s}$$

Note: this does not update $P$, so it does not account for growing uncertainty over the horizon. This is a known limitation.

---

## The Full Loop

$$\boxed{\mathbf{s}_{t-1},\ P_{t-1}} \xrightarrow{\text{Predict: } F,\ Q} \boxed{\hat{\mathbf{s}}_t,\ P_t^{-}} \xrightarrow{\text{Update: } \mathbf{z}_t,\ H,\ R,\ K} \boxed{\mathbf{s}_t,\ P_t}$$

Repeat every frame.

---

## Summary Table

| Step | What happens | Key equation |
|------|-------------|--------------|
| Init | Set state from first detection | $\mathbf{s}_0 = [x, y, z, 0, 0, 0]^\top$ |
| Predict state | Use velocity to estimate next position | $\hat{\mathbf{s}}_t = F \cdot \mathbf{s}_{t-1}$ |
| Predict uncertainty | Uncertainty grows slightly | $P_t^{-} = F P_{t-1} F^\top + Q$ |
| Residual | How wrong was the prediction? | $\mathbf{y}_t = \mathbf{z}_t - H \hat{\mathbf{s}}_t$ |
| Kalman gain | How much to trust sensor vs model? | $K = P_t^{-} H^\top (H P_t^{-} H^\top + R)^{-1}$ |
| Update state | Correct prediction using measurement | $\mathbf{s}_t = \hat{\mathbf{s}}_t + K \mathbf{y}_t$ |
| Update uncertainty | Uncertainty shrinks after measurement | $P_t = (I - KH) P_t^{-}$ |
| Coast | No detection - skip update, predict only | - |
| Forward predict | Where will ball be in 0.2 s? | $\hat{p}_{t+h} = p + v \cdot h$ |
