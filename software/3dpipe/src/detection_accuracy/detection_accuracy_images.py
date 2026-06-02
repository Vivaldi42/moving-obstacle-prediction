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
    ("cap_046_left.png", "cap_046_depth.npy",         0.1,  0.175,   0.67),
    ("cap_047_left.png", "cap_047_depth.npy",         0.3,  0.175,   0.67),
]

# ---------------------------------------------------------------------------

def load_intrinsics() -> tuple[float, float, float, float]:
    path = os.path.join(DATA_DIR, "intrinsics.json")
    data = json.load(open(path))
    return data["fx"], data["fy"], data["cx"], data["cy"]


def depth_to_xyz(depth: np.ndarray, fx: float, fy: float, cx: float, cy: float) -> np.ndarray:
    """Convert a (H, W) depth map to a (H, W, 3) XYZ map matching sl.MEASURE.XYZ layout."""
    H, W = depth.shape
    us = np.arange(W, dtype=np.float32)
    vs = np.arange(H, dtype=np.float32)
    uu, vv = np.meshgrid(us, vs)
    invalid = ~np.isfinite(depth) | (depth <= 0)

    z = np.where(invalid, np.nan, depth)
    x = np.where(invalid, np.nan, (uu - cx) * depth / fx)
    y = np.where(invalid, np.nan, (vv - cy) * depth / fy)

    return np.stack([x, y, z], axis=-1).astype(np.float32)


# ---------------------------------------------------------------------------

model = load_model("yolov8x.pt")
fx, fy, cx, cy = load_intrinsics()

has_truth = any(true_x is not None for _, _, true_x, _, _ in CAPTURES)

header = f"{'#':<4} {'Image':<25} {'Det':>5}   {'X (m)':>8} {'Y (m)':>8} {'Z (m)':>8}"
if has_truth:
    header += f"   {'Err X':>8} {'Err Y':>8} {'Err Z':>8}   {'|Error|':>8}"
print(header)
print("-" * (65 + (42 if has_truth else 0)))

records = []

for i, (left_file, depth_file, true_x, true_y, true_z) in enumerate(CAPTURES):
    rec = {"idx": i + 1, "name": left_file, "true_x": true_x, "true_y": true_y, "true_z": true_z}

    img_bgr = cv2.imread(os.path.join(DATA_DIR, left_file))
    if img_bgr is None:
        print(f"{i+1:<4} {left_file:<25} ERROR: cannot load image")
        rec["status"] = "error"
        records.append(rec)
        continue

    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    depth = np.load(os.path.join(DATA_DIR, depth_file)).squeeze()
    xyz_map = depth_to_xyz(depth, fx, fy, cx, cy)

    bbox = detect_ball_bbox(model, img_rgb)
    if bbox is None:
        print(f"{i+1:<4} {left_file:<25} {'no':>5}")
        rec["status"] = "missed"
        records.append(rec)
        continue

    x1, y1, x2, y2 = bbox
    result = calc_ball_3d_position(xyz_map, x1, y1, x2, y2)

    if result is None:
        print(f"{i+1:<4} {left_file:<25} {'bad depth':>5}")
        rec["status"] = "bad_depth"
        records.append(rec)
        continue

    camera_x, camera_y, camera_z = result
    rec["cam_x"] = camera_x
    rec["cam_y"] = camera_y
    rec["cam_z"] = camera_z

    row = f"{i+1:<4} {left_file:<25} {'yes':>5}   {camera_x:>8.2f} {camera_y:>8.2f} {camera_z:>8.2f}"

    if true_x is not None and true_y is not None and true_z is not None:
        err_x = camera_x - true_x
        err_y = camera_y - true_y
        err_z = camera_z - true_z
        dist = float(np.linalg.norm([err_x, err_y, err_z]))
        row += f"   {err_x:>+8.2f} {err_y:>+8.2f} {err_z:>+8.2f}   {dist:>7.2f}"
        rec.update({"err_x": err_x, "err_y": err_y, "err_z": err_z, "dist": dist, "status": "ok"})
    else:
        rec["status"] = "ok_no_truth"

    records.append(rec)
    print(row)

# ---------------------------------------------------------------------------
# Summary statistics

ok = [r for r in records if r.get("status") == "ok"]
if ok:
    errs_x = np.array([r["err_x"] for r in ok])
    errs_y = np.array([r["err_y"] for r in ok])
    errs_z = np.array([r["err_z"] for r in ok])
    dists   = np.array([r["dist"]  for r in ok])

    n_total  = len(records)
    n_missed = sum(1 for r in records if r.get("status") == "missed")
    n_ok     = len(ok)

    print()
    print(f"Detection rate : {n_ok}/{n_total}  ({n_missed} out of frame)")
    print(f"Mean |Error|   : {dists.mean()*100:.1f} cm  (std {dists.std()*100:.1f} cm)")
    print(f"Mean Err X     : {errs_x.mean()*100:+.1f} cm  (std {errs_x.std()*100:.1f} cm)")
    print(f"Mean Err Y     : {errs_y.mean()*100:+.1f} cm  (std {errs_y.std()*100:.1f} cm)")
    print(f"Mean Err Z     : {errs_z.mean()*100:+.1f} cm  (std {errs_z.std()*100:.1f} cm)")

# ---------------------------------------------------------------------------
# Visualization

if ok:
    z_vals = sorted(set(r["true_z"] for r in ok))
    palette = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    color_map = dict(zip(z_vals, palette))

    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    fig.suptitle("Ball Detection Accuracy", fontsize=14, fontweight="bold")

    panels = [
        ("err_x", "Err X (cm)", axes[0, 0]),
        ("err_y", "Err Y (cm)", axes[0, 1]),
        ("err_z", "Err Z (cm)", axes[1, 0]),
        ("dist",  "|Error| (cm)", axes[1, 1]),
    ]

    for key, ylabel, ax in panels:
        for z in z_vals:
            group = [r for r in ok if r["true_z"] == z]
            y_heights = sorted(set(r["true_y"] for r in group), reverse=True)
            for y_h in y_heights:
                sub = sorted([r for r in group if r["true_y"] == y_h], key=lambda r: r["true_x"])
                xs = [r["true_x"] for r in sub]
                ys = [r[key] * 100 for r in sub]
                is_floor = y_h == max(y_heights)
                marker    = "o" if is_floor else "s"
                linestyle = "-" if is_floor else "--"
                label = f"Z={z:.2f}m" + ("" if is_floor else f", Y={y_h:.3f}m")
                ax.plot(xs, ys, marker=marker, linestyle=linestyle,
                        color=color_map[z], label=label, markersize=5, linewidth=1.5)

        ax.axhline(0, color="gray", linestyle="--", linewidth=0.8)
        ax.set_xlabel("True X (m)")
        ax.set_ylabel(ylabel)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "accuracy_plot.png")
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nPlot saved to {out_path}")
