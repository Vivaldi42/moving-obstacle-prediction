"""Scalar 1D Kalman filter, matching Part 1 of docs/kalman_filter/kalman_filter.md.

State is a single number (x position) plus its variance (P). Velocity is
not part of the state here - it is passed in each step as v, e.g. estimated
externally from consecutive corrected positions. See demo.py for usage.
"""

from dataclasses import dataclass


@dataclass
class StepResult:
    x_pred: float  # x^-_k - predicted position, before the measurement
    p_pred: float  # P^-_k - predicted variance, before the measurement
    k: float        # K - Kalman gain
    y: float        # y_k - residual (measurement - prediction)
    x: float        # x_k - corrected position
    p: float        # P_k - corrected variance


class KalmanFilter1D:
    def __init__(self, x0: float, p0: float, q: float, r: float) -> None:
        self.x = x0  # current position estimate
        self.p = p0  # current variance
        self.q = q   # process noise
        self.r = r   # measurement noise

    def step(self, z: float, v: float, dt: float) -> StepResult:
        # Step 1 - predict state
        x_pred = self.x + v * dt

        # Step 2 - predict uncertainty
        p_pred = self.p + self.q

        # Step 3 - Kalman gain
        k = p_pred / (p_pred + self.r)

        # Step 4 - update state
        y = z - x_pred
        x = x_pred + k * y

        # Step 5 - update uncertainty
        p = (1 - k) * p_pred

        self.x = x
        self.p = p

        return StepResult(x_pred=x_pred, p_pred=p_pred, k=k, y=y, x=x, p=p)
