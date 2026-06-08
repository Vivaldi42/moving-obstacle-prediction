import csv
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pyzed.sl as sl
from pipeline import open_svo, grab_frame, load_model, detect, resolve_xyz, get_intrinsics, project_to_pixel, BallKalmanFilter

SVO_PATH  = "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2"
OUT_DIR   = "/app/output"
CSV_PATH      = f"{OUT_DIR}/ground_truth.csv"
PRED_CSV_PATH = f"{OUT_DIR}/predictions.csv"
VIDEO_PATH    = f"{OUT_DIR}/ground_truth.mp4"

def extract_positions(svo_path, model):
    cam = open_svo(svo_path)
    mat_rgb = sl.Mat()
    mat_xyz = sl.Mat()

    positions = {}
    frame_idx = 0

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        left_rgb, xyz_map = result
        detection = detect(model, left_rgb)

        if detection is not None:
            cx, cy = detection
            positions[frame_idx] = resolve_xyz(xyz_map, cx, cy)
        else:
            positions[frame_idx] = None

        frame_idx += 1

    cam.close()
    return positions

def interpolate_positions(positions):
    valid_frames = sorted(f for f, xyz in positions.items() if xyz is not None)

    result = dict(positions)

    for i in range(len(valid_frames) - 1):
        f_start = valid_frames[i]
        f_end   = valid_frames[i + 1]

        if f_end - f_start <= 1:
            continue

        x0, y0, z0 = positions[f_start]
        x1, y1, z1 = positions[f_end]
        gap = f_end - f_start

        for f in range(f_start + 1, f_end):
            t = (f - f_start) / gap
            result[f] = (
                x0 + t * (x1 - x0),
                y0 + t * (y1 - y0),
                z0 + t * (z1 - z0),
            )

    return result


def run_kf(svo_path, model):
    cam = open_svo(svo_path)
    mat_rgb = sl.Mat()
    mat_xyz = sl.Mat()
    kf = BallKalmanFilter(dt=1/30)

    predictions = {}
    frame_idx = 0
    missed = 0

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        if kf.initialized:
            kf.predict()

        left_rgb, xyz_map = result
        det = detect(model, left_rgb)

        if det is not None:
            cx, cy = det
            xyz = resolve_xyz(xyz_map, cx, cy)
            if xyz is not None:
                x, y, z = xyz
                if not kf.initialized:
                    kf.init(x, y, z)
                    kf.predict()
                kf.correct(x, y, z)
            missed = 0
        else:
            missed += 1

        if kf.initialized and missed < 5:
            predictions[frame_idx] = kf.predict_ahead(0.2)

        frame_idx += 1

    cam.close()
    return predictions


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    model = load_model("yolov8x.pt")
    positions = extract_positions(SVO_PATH, model)
    positions = interpolate_positions(positions)

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "x", "y", "z"])
        for frame_idx, xyz in positions.items():
            if xyz is not None:
                x, y, z = xyz
                writer.writerow([frame_idx, round(x, 3), round(y, 3), round(z, 3)])
            else:
                writer.writerow([frame_idx, "", "", ""])

    print(f"Saved {len(positions)} rows to {CSV_PATH}")

    predictions = run_kf(SVO_PATH, model)

    with open(PRED_CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "pred_x", "pred_y", "pred_z"])
        for frame_idx, (px, py, pz) in predictions.items():
            writer.writerow([frame_idx, round(px, 3), round(py, 3), round(pz, 3)])

    print(f"Saved {len(predictions)} rows to {PRED_CSV_PATH}")

    cam = open_svo(SVO_PATH)
    fx, fy, cx_cam, cy_cam = get_intrinsics(cam)
    mat_rgb = sl.Mat()
    mat_xyz = sl.Mat()
    writer = cv2.VideoWriter(VIDEO_PATH, cv2.VideoWriter.fourcc(*"mp4v"), 30, (1920, 1080))

    frame_idx = 0
    trail = []

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        left_rgb, _ = result
        frame_bgr = cv2.cvtColor(left_rgb, cv2.COLOR_RGB2BGR)

        gt = positions.get(frame_idx)
        if gt is not None:
            x, y, z = gt
            pixel = project_to_pixel(x, y, z, fx, fy, cx_cam, cy_cam)
            if pixel is not None:
                trail.append(pixel)

        for j in range(1, len(trail)):
            cv2.line(frame_bgr, trail[j - 1], trail[j], (0, 0, 255), 2)

        if trail:
            cv2.circle(frame_bgr, trail[-1], 10, (0, 0, 255), -1)

        writer.write(frame_bgr)
        frame_idx += 1

    writer.release()
    cam.close()
    print(f"Saved video to {VIDEO_PATH}")

    frames, errors = [], []
    for frame_idx, (px, py, pz) in predictions.items():
        gt = positions.get(frame_idx + 6)
        if gt is not None:
            gx, gy, gz = gt
            fde = float(np.linalg.norm([px - gx, py - gy, pz - gz]))
            frames.append(frame_idx)
            errors.append(fde)

    plt.figure()
    plt.plot(frames, errors)
    plt.xlabel("Frame")
    plt.ylabel("FDE (m)")
    plt.title("KF prediction error over time")
    plt.savefig(f"{OUT_DIR}/fde_plot.png")
    plt.close()
    print(f"Saved plot to {OUT_DIR}/fde_plot.png")


