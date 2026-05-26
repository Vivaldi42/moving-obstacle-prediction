import csv
import os
import numpy as np
import matplotlib.pyplot as plt
import pyzed.sl as sl
from pipeline import open_svo, grab_frame, load_model, detect, object_3d_position, BallKalmanFilter

SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2"
OUTPUT_DIR = "/app/output"
FPS = 30
PREDICTION_HORIZON = 0.2


def run_pipeline(svo_path: str, model) -> tuple[dict, dict]:
    cam = open_svo(svo_path)
    mat_rgb = sl.Mat()
    mat_xyz = sl.Mat()
    kf = BallKalmanFilter(dt=1 / FPS)

    gt = {}
    predictions = {}
    frame_idx = 0
    missed = 0
    corrections = 0

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        left_rgb, xyz_map = result

        if kf.initialized:
            kf.predict()

        detection = detect(model, left_rgb)
        if detection is not None:
            x1, y1, x2, y2 = detection
            xyz = object_3d_position(xyz_map, x1, y1, x2, y2)
            if xyz is not None:
                if not kf.initialized:
                    kf.init(*xyz)
                    kf.predict()
                kf.correct(*xyz)
                gt[frame_idx] = xyz
                missed = 0
                corrections += 1
        else:
            missed += 1

        if corrections >= 2 and missed < 5:
            predictions[frame_idx] = kf.predict_ahead(PREDICTION_HORIZON)

        frame_idx += 1

    cam.close()
    return gt, predictions


def compute_fde(
    gt: dict,
    predictions: dict,
) -> tuple[list[int], list[float]]:
    lookahead = round(PREDICTION_HORIZON * FPS)

    frames, errors = [], []
    for frame_idx, (px, py, pz) in predictions.items():
        gt_xyz = gt.get(frame_idx + lookahead)
        if gt_xyz is None:
            continue
        gx, gy, gz = gt_xyz
        fde = float(np.linalg.norm([px - gx, py - gy, pz - gz]))
        frames.append(frame_idx)
        errors.append(fde)

    return frames, errors


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model = load_model("yolov8x.pt")

    gt, predictions = run_pipeline(SVO_PATH, model)

    with open(f"{OUTPUT_DIR}/ground_truth.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "x", "y", "z"])
        for frame_idx, (x, y, z) in gt.items():
            writer.writerow([frame_idx, round(x, 3), round(y, 3), round(z, 3)])

    with open(f"{OUTPUT_DIR}/predictions.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "pred_x", "pred_y", "pred_z"])
        for frame_idx, (px, py, pz) in predictions.items():
            writer.writerow([frame_idx, round(px, 3), round(py, 3), round(pz, 3)])

    frames, errors = compute_fde(gt, predictions)

    plt.figure()
    plt.plot(frames, errors)
    plt.xlabel("Frame")
    plt.ylabel("FDE (m)")
    plt.title("KF prediction error over time")
    plt.savefig(f"{OUTPUT_DIR}/fde_plot.png")
    plt.close()

    print(f"Frames evaluated: {len(errors)}")
    print(f"Mean FDE: {np.mean(errors):.3f} m")
    print(f"Max FDE:  {np.max(errors):.3f} m")
