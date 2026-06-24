"""Demo: 1D Kalman filter tracking a ball's x position.

Generates a synthetic ground-truth trajectory (constant velocity), adds
camera-like measurement noise, then runs KalmanFilter1D frame by frame.
Prints a per-frame table and saves a plot comparing true / measured /
filtered x over time.

Velocity is not measured, so it is estimated each frame from the last two
corrected positions and fed into the next predict step.
"""

import numpy as np
import matplotlib.pyplot as plt

from kalman_1d import KalmanFilter1D

# Parameters, matching the values used in docs/kalman_filter/kalman_filter.md
DT = 1 / 30          # 30 fps
Q = 0.0001           # process noise (m^2)
R = 0.000064         # measurement noise, zed_noise config (m^2) - large R => little trust in camera
P0 = 1.0             # initial variance (m^2)

N_FRAMES = 30        # 1 second of motion
X0_TRUE = 1.0        # starting x position (m)
V_TRUE = 0.6         # true x velocity (m/s)

RNG = np.random.default_rng(42)


def main() -> None:
    # position = start + velocity * time applied to all frames at once
    x_true = X0_TRUE + V_TRUE * np.arange(N_FRAMES) * DT

    # simulated camera measurements
    z = x_true + RNG.normal(0.0, np.sqrt(R), size=N_FRAMES)

    kf = KalmanFilter1D(x0=z[0], p0=P0, q=Q, r=R)

    x_filtered = np.empty(N_FRAMES)
    sigma = np.empty(N_FRAMES)
    x_filtered[0] = kf.x
    sigma[0] = np.sqrt(kf.p)

    v_est = 0.0  # velocity unknown at the first frame

    print(f"{'k':>2} {'x_true':>8} {'z':>8} {'x_pred':>8} {'K':>6} {'y':>8} {'x':>8} {'sigma':>8}")
    print(f"{0:>2} {x_true[0]:>8.4f} {z[0]:>8.4f} {'':>8} {'':>6} {'':>8} {kf.x:>8.4f} {sigma[0]:>8.4f}")

    for k in range(1, N_FRAMES):
        result = kf.step(z[k], v_est, DT)

        x_filtered[k] = result.x
        sigma[k] = np.sqrt(result.p)

        print(
            f"{k:>2} {x_true[k]:>8.4f} {z[k]:>8.4f} {result.x_pred:>8.4f} "
            f"{result.k:>6.3f} {result.y:>8.4f} {result.x:>8.4f} {sigma[k]:>8.4f}"
        )

        # Velocity is not measured, estimate it from consecutive corrected positions
        v_est = (x_filtered[k] - x_filtered[k - 1]) / DT

    frames = np.arange(N_FRAMES)

    fig, (ax_pos, ax_sigma) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

    ax_pos.plot(frames, x_true, label="true x", color="black", linewidth=2)
    ax_pos.scatter(frames, z, label="camera measurement", color="tab:orange", s=15)
    ax_pos.plot(frames, x_filtered, label="filtered x", color="tab:blue", linewidth=2)
    ax_pos.set_ylabel("x (m)")
    ax_pos.set_title("1D Kalman filter: true vs measured vs filtered x")
    ax_pos.legend()

    ax_sigma.plot(frames, sigma, color="tab:green")
    ax_sigma.set_xlabel("frame")
    ax_sigma.set_ylabel("sigma (m)")
    ax_sigma.set_title("Position uncertainty over time")

    fig.tight_layout()

    out_path = "demo_plot.png"
    fig.savefig(out_path, dpi=150)
    print(f"\nPlot saved to {out_path}")


if __name__ == "__main__":
    main()
