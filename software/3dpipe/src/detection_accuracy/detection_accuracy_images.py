"""
Measures YOLO and ZED detection accuracy from captured image/depth pairs.
Fill in CAPTURES with filenames and manual measurements, then run.

X = left/right (right is positive), Y = up/down (down is positive),
Z = distance from camera. Measurements are in metres (m).

Leave None for axes that have not been measured yet.
"""

import json
import os
import sys

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from pipeline import detect_ball_bbox, load_model, calc_ball_3d_position

DATA_DIR = "/datasets/Dataset_2/Clean/Detection_Accuracy"

CAPTURES = [
    # (left_image,           depth_file,             true_x, true_y, true_z)
    ("cap_001_left.png", "cap_001_depth.npy",         0.7,   0.28,   0.77),
    ("cap_002_left.png", "cap_002_depth.npy",         0.6,   0.28,   0.77),
    ("cap_003_left.png", "cap_003_depth.npy",         0.5,   0.28,   0.77),
    ("cap_004_left.png", "cap_004_depth.npy",         0.4,   0.28,   0.77),
    ("cap_005_left.png", "cap_005_depth.npy",         0.3,   0.28,   0.77),
    ("cap_006_left.png", "cap_006_depth.npy",         0.2,   0.28,   0.77),
    ("cap_007_left.png", "cap_007_depth.npy",         0.1,   0.28,   0.77),
    ("cap_008_left.png", "cap_008_depth.npy",         0.0,   0.28,   0.77),
    ("cap_009_left.png", "cap_009_depth.npy",        -0.1,   0.28,   0.77),
    ("cap_010_left.png", "cap_010_depth.npy",        -0.2,   0.28,   0.77),
    ("cap_011_left.png", "cap_011_depth.npy",        -0.3,   0.28,   0.77),
    ("cap_012_left.png", "cap_012_depth.npy",        -0.4,   0.28,   0.77),
    ("cap_013_left.png", "cap_013_depth.npy",        -0.5,   0.28,   0.77),
    ("cap_014_left.png", "cap_014_depth.npy",        -0.6,   0.28,   0.77),
    ("cap_015_left.png", "cap_015_depth.npy",        -0.7,   0.28,   0.77),
    ("cap_016_left.png", "cap_016_depth.npy",         0.7,   0.28,   0.67),
    ("cap_017_left.png", "cap_017_depth.npy",         0.6,   0.28,   0.67),
    ("cap_018_left.png", "cap_018_depth.npy",         0.5,   0.28,   0.67),
    ("cap_019_left.png", "cap_019_depth.npy",         0.4,   0.28,   0.67),
    ("cap_020_left.png", "cap_020_depth.npy",         0.3,   0.28,   0.67),
    ("cap_021_left.png", "cap_021_depth.npy",         0.2,   0.28,   0.67),
    ("cap_022_left.png", "cap_022_depth.npy",         0.1,   0.28,   0.67),
    ("cap_023_left.png", "cap_023_depth.npy",         0.0,   0.28,   0.67),
    ("cap_024_left.png", "cap_024_depth.npy",        -0.1,   0.28,   0.67),
    ("cap_025_left.png", "cap_025_depth.npy",        -0.2,   0.28,   0.67),
    ("cap_026_left.png", "cap_026_depth.npy",        -0.3,   0.28,   0.67),
    ("cap_027_left.png", "cap_027_depth.npy",        -0.4,   0.28,   0.67),
    ("cap_028_left.png", "cap_028_depth.npy",        -0.5,   0.28,   0.67),
    ("cap_029_left.png", "cap_029_depth.npy",        -0.6,   0.28,   0.67),
    ("cap_030_left.png", "cap_030_depth.npy",        -0.7,   0.28,   0.67),
    ("cap_031_left.png", "cap_031_depth.npy",         0.7,   0.28,   0.57),
    ("cap_032_left.png", "cap_032_depth.npy",         0.6,   0.28,   0.57),
    ("cap_033_left.png", "cap_033_depth.npy",         0.5,   0.28,   0.57),
    ("cap_034_left.png", "cap_034_depth.npy",         0.4,   0.28,   0.57),
    ("cap_035_left.png", "cap_035_depth.npy",         0.3,   0.28,   0.57),
    ("cap_036_left.png", "cap_036_depth.npy",         0.2,   0.28,   0.57),
    ("cap_037_left.png", "cap_037_depth.npy",         0.1,   0.28,   0.57),
    ("cap_038_left.png", "cap_038_depth.npy",         0.0,   0.28,   0.57),
    ("cap_039_left.png", "cap_039_depth.npy",        -0.1,   0.28,   0.57),
    ("cap_040_left.png", "cap_040_depth.npy",        -0.2,   0.28,   0.57),
    ("cap_041_left.png", "cap_041_depth.npy",        -0.3,   0.28,   0.57),
    ("cap_042_left.png", "cap_042_depth.npy",        -0.4,   0.28,   0.57),
    ("cap_043_left.png", "cap_043_depth.npy",        -0.5,   0.28,   0.57),
    ("cap_044_left.png", "cap_044_depth.npy",        -0.6,   0.28,   0.57),
    ("cap_045_left.png", "cap_045_depth.npy",        -0.7,   0.28,   0.57),
]

# ---------------------------------------------------------------------------

def depth_to_xyz(depth: np.ndarray, fx: float, fy: float, cx: float, cy: float) -> np.ndarray:
    """Convert a (H, W) depth map to a (H, W, 3) XYZ map matching sl.MEASURE.XYZ layout."""
    H, W = depth.shape
    uu, vv = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    invalid = ~np.isfinite(depth) | (depth <= 0)
    z = np.where(invalid, np.nan, depth)
    x = np.where(invalid, np.nan, (uu - cx) * depth / fx)
    y = np.where(invalid, np.nan, (vv - cy) * depth / fy)
    return np.stack([x, y, z], axis=-1).astype(np.float32)


def process_capture(
    i: int,
    left_file: str, depth_file: str,
    true_x: float | None, true_y: float | None, true_z: float | None,
    model, fx: float, fy: float, cx: float, cy: float,
) -> dict:
    base = {"idx": i + 1, "name": left_file, "true_x": true_x, "true_y": true_y, "true_z": true_z}
    prefix = f"{i+1:<4} {left_file:<25}"

    img_bgr = cv2.imread(os.path.join(DATA_DIR, left_file))
    if img_bgr is None:
        print(f"{prefix} ERROR: cannot load image")
        return {**base, "status": "error"}

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    xyz_map = depth_to_xyz(np.load(os.path.join(DATA_DIR, depth_file)).squeeze(), fx, fy, cx, cy)

    bbox = detect_ball_bbox(model, img_rgb)
    if bbox is None:
        print(f"{prefix} {'no':>5}")
        return {**base, "status": "missed"}

    result = calc_ball_3d_position(xyz_map, *bbox)
    if result is None:
        print(f"{prefix} {'bad depth':>5}")
        return {**base, "status": "bad_depth"}

    camera_x, camera_y, camera_z = result
    row = f"{prefix} {'yes':>5}   {camera_x:>8.2f} {camera_y:>8.2f} {camera_z:>8.2f}"

    if true_x is not None and true_y is not None and true_z is not None:
        err_x, err_y, err_z = camera_x - true_x, camera_y - true_y, camera_z - true_z
        dist = float(np.linalg.norm([err_x, err_y, err_z]))
        row += f"   {err_x:>+8.2f} {err_y:>+8.2f} {err_z:>+8.2f}   {dist:>7.2f}"
        print(row)
        return {**base, "cam_x": camera_x, "cam_y": camera_y, "cam_z": camera_z,
                "err_x": err_x, "err_y": err_y, "err_z": err_z, "dist": dist, "status": "ok"}

    print(row)
    return {**base, "cam_x": camera_x, "cam_y": camera_y, "cam_z": camera_z, "status": "ok_no_truth"}


def print_summary(records: list[dict]) -> None:
    ok = [r for r in records if r.get("status") == "ok"]
    if not ok:
        return
    errs_x = np.array([r["err_x"] for r in ok])
    errs_y = np.array([r["err_y"] for r in ok])
    errs_z = np.array([r["err_z"] for r in ok])
    dists  = np.array([r["dist"]  for r in ok])
    n_missed = sum(1 for r in records if r.get("status") == "missed")
    print(f"\nDetection rate : {len(ok)}/{len(records)}  ({n_missed} out of frame)")
    print(f"Mean |Error|   : {dists.mean()*100:.1f} cm  (std {dists.std()*100:.1f} cm)")
    print(f"Mean Err X     : {errs_x.mean()*100:+.1f} cm  (std {errs_x.std()*100:.1f} cm)")
    print(f"Mean Err Y     : {errs_y.mean()*100:+.1f} cm  (std {errs_y.std()*100:.1f} cm)")
    print(f"Mean Err Z     : {errs_z.mean()*100:+.1f} cm  (std {errs_z.std()*100:.1f} cm)")



def plot_error_vs_position(
    records: list[dict],
    err_key: str,
    axis_label: str,
    fig_title: str,
    out_filename: str,
    y_lim: tuple[float, float] | None = None,
) -> None:
    ok = [r for r in records if r.get("status") == "ok"]
    if not ok:
        return

    z_vals = sorted(set(r["true_z"] for r in ok))
    colors = {z: c for z, c in zip(z_vals, ["#1f77b4", "#ff7f0e", "#2ca02c"])}

    RULER_UNCERTAINTY = 0.01  # m

    fig, axes = plt.subplots(1, 3, figsize=(20, 6), sharey=True)
    fig.suptitle(fig_title, fontsize=13, fontweight="bold")

    if y_lim is not None:
        y_min, y_max = y_lim
    else:
        all_errs = [r[err_key] for r in ok]
        margin = 0.005
        y_min = min(all_errs) - margin
        y_max = max(all_errs) + margin

    for ax, z in zip(axes, z_vals):
        grp = sorted([r for r in ok if r["true_z"] == z], key=lambda r: r["true_x"])
        xs = [r["true_x"] for r in grp]
        ys = [r[err_key] for r in grp]

        mean_y = np.mean(ys)
        ax.axhspan(-RULER_UNCERTAINTY, RULER_UNCERTAINTY, color="gray", alpha=0.12, zorder=1,
                   label=f"±{RULER_UNCERTAINTY:.2f} m ruler uncertainty")
        ax.scatter(xs, ys, color=colors[z], marker="o", s=45, zorder=3)
        ax.axhline(mean_y, color=colors[z], linestyle="--", linewidth=1.2, zorder=2)
        ax.axhline(0, color="gray", linestyle="-", linewidth=0.8)
        ax.text(1.0, -0.16, f"mean = {mean_y:.2f} m", color=colors[z], fontsize=9,
                ha="right", va="top", transform=ax.transAxes, clip_on=False)
        ax.set_xlabel("True X position (m)")
        ax.set_xticks(np.arange(-0.7, 0.8, 0.1))
        ax.set_yticks(np.arange(round(y_min, 2), round(y_max + 0.01, 2), 0.01))
        ax.set_ylim(y_min, y_max)
        ax.tick_params(axis="x", labelrotation=45)
        ax.tick_params(axis="y", labelleft=True)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(0.0, -0.16),
                  borderaxespad=0)
        ax.set_title(f"Y = 0.28 m,  Z = {z:.2f} m", fontsize=12, pad=8)

    for ax in axes:
        ax.set_ylabel(axis_label)

    plt.tight_layout(rect=[0, 0.10, 1, 1])
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, out_filename)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved to {out_path}")


def main() -> None:
    model = load_model("yolov8x.pt")
    intr = json.load(open(os.path.join(DATA_DIR, "intrinsics.json")))
    fx, fy, cx, cy = intr["fx"], intr["fy"], intr["cx"], intr["cy"]

    has_truth = any(true_x is not None for _, _, true_x, _, _ in CAPTURES)
    header = f"{'#':<4} {'Image':<25} {'Det':>5}   {'X (m)':>8} {'Y (m)':>8} {'Z (m)':>8}"
    if has_truth:
        header += f"   {'Err X':>8} {'Err Y':>8} {'Err Z':>8}   {'|Error|':>8}"
    print(header)
    print("-" * (65 + (42 if has_truth else 0)))

    records = [
        process_capture(i, *cap, model, fx, fy, cx, cy)
        for i, cap in enumerate(CAPTURES)
    ]

    print_summary(records)

    ok = [r for r in records if r.get("status") == "ok"]
    margin = 0.005
    all_vals = [r[k] for r in ok for k in ("err_x", "err_y", "err_z", "dist")]
    shared_y_lim = (min(all_vals) - margin, max(all_vals) + margin)

    plot_error_vs_position(records, "err_x", "X error (m)", "X Error vs True X Position", "x_error_vs_position.png", shared_y_lim)
    plot_error_vs_position(records, "err_y", "Y error (m)", "Y Error vs True X Position", "y_error_vs_position.png", shared_y_lim)
    plot_error_vs_position(records, "err_z", "Z error (m)", "Z Error vs True X Position", "z_error_vs_position.png", shared_y_lim)
    plot_error_vs_position(records, "dist",  "|Error| (m)", "|Error| vs True X Position",  "abs_error_vs_position.png", shared_y_lim)


if __name__ == "__main__":
    main()
