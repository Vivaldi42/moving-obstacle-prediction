import csv
import os
import subprocess
import time
import cv2
import numpy as np
import matplotlib.pyplot as plt
import psutil
import pyzed.sl as sl
from collections import deque
from pipeline import (
    open_svo, get_intrinsics, grab_frame,
    load_model, detect_ball_bbox, calc_ball_3d_position,
    project_to_pixel, BallKalmanFilter,
)

try:
    import torch
    _TORCH_CUDA = torch.cuda.is_available()
except ImportError:
    _TORCH_CUDA = False

SVO_PATH = "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-34-15.svo2"
OUTPUT_DIR = "/app/output"
FPS = 30
PREDICTION_HORIZON = 0.2
PREDICTION_STEPS = round(PREDICTION_HORIZON * FPS)  # 6
MAX_MISSED = 5
VISUALIZE = True


def run_pipeline(
    svo_path: str,
    model,
    visualize: bool = False,
    output_path: str | None = None,
) -> tuple[dict, dict, dict]:
    """Run the full pipeline on one SVO file.

    Returns:
        ground_truth  - {frame_idx: (x, y, z)}
        predictions   - {frame_idx: [(px, py, pz), ...]} with PREDICTION_STEPS entries per frame
        metrics       - latency, throughput, RAM, GPU memory
    """
    cam = open_svo(svo_path)
    mat_rgb = sl.Mat()
    mat_xyz = sl.Mat()
    kf = BallKalmanFilter(dt=1 / FPS)

    ground_truth: dict = {}
    predictions: dict = {}
    frame_idx = 0
    missed = 0
    corrections = 0

    fx = fy = cx_cam = cy_cam = 0.0
    trail: deque = deque()
    pred_trail: deque = deque()
    pred_buffer: dict = {}
    writer: cv2.VideoWriter | None = None
    tmp_path: str = ""

    latencies: list[float] = []
    process = psutil.Process()
    ram_samples: list[float] = []

    if _TORCH_CUDA:
        torch.cuda.reset_peak_memory_stats()

    if visualize:
        assert output_path is not None
        fx, fy, cx_cam, cy_cam = get_intrinsics(cam)
        tmp_path = output_path + ".tmp.mp4"
        writer = cv2.VideoWriter(
            tmp_path,
            cv2.VideoWriter.fourcc(*"mp4v"),
            FPS,
            (1920, 1080),
        )

    t_pipeline_start = time.perf_counter()

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        # Latency: from frame received to prediction output
        t_frame_start = time.perf_counter()

        left_rgb, xyz_map = result

        if kf.initialized:
            kf.predict()

        detected_ball_bbox = detect_ball_bbox(model, left_rgb)
        smoothed_xyz: tuple[float, float, float] | None = None

        if detected_ball_bbox is not None:
            x1, y1, x2, y2 = detected_ball_bbox
            ball_position_xyz = calc_ball_3d_position(xyz_map, x1, y1, x2, y2)
            if ball_position_xyz is not None:
                x, y, z = ball_position_xyz
                if not kf.initialized:
                    kf.reset(x, y, z)
                    kf.predict()
                smoothed_xyz = kf.correct(x, y, z)
                ground_truth[frame_idx] = ball_position_xyz
                missed = 0
                corrections += 1
        else:
            missed += 1

        pred_sequence: list[tuple[float, float, float]] | None = None
        if corrections >= 2 and missed < MAX_MISSED:
            pred_sequence = [
                kf.predict_ahead(s / FPS)
                for s in range(1, PREDICTION_STEPS + 1)
            ]
            predictions[frame_idx] = pred_sequence

        latencies.append((time.perf_counter() - t_frame_start) * 1000)
        ram_samples.append(process.memory_info().rss / 1e6)

        if visualize:
            assert writer is not None
            frame_bgr = cv2.cvtColor(left_rgb, cv2.COLOR_RGB2BGR)
            current_pixel: tuple[int, int] | None = None
            pred_xyz = pred_sequence[-1] if pred_sequence is not None else None

            if smoothed_xyz is not None:
                sx, sy, sz = smoothed_xyz
                current_pixel = project_to_pixel(sx, sy, sz, fx, fy, cx_cam, cy_cam)
            elif kf.initialized and missed > 0 and missed < MAX_MISSED:
                cpx, cpy, cpz = kf.predict()
                current_pixel = project_to_pixel(cpx, cpy, cpz, fx, fy, cx_cam, cy_cam)

            if current_pixel is not None:
                trail.append(current_pixel)

            for i in range(1, len(trail)):
                cv2.line(frame_bgr, trail[i - 1], trail[i], (0, 255, 0), 2)

            if current_pixel is not None:
                color = (0, 255, 0) if missed == 0 else (0, 165, 255)
                cv2.circle(frame_bgr, current_pixel, 15, color, 3)
                if kf.initialized:
                    cx, cy, cz = (
                        float(kf.kf.statePost[0, 0]),
                        float(kf.kf.statePost[1, 0]),
                        float(kf.kf.statePost[2, 0]),
                    )
                    label = f"x:{cx:.2f} y:{cy:.2f} z:{cz:.2f}m"
                    cv2.putText(
                        frame_bgr, label,
                        (current_pixel[0] + 20, current_pixel[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
                    )

            if pred_xyz is not None:
                px, py, pz = pred_xyz
                pred_buffer[frame_idx + PREDICTION_STEPS] = pred_xyz
                pred_pixel = project_to_pixel(px, py, pz, fx, fy, cx_cam, cy_cam)
                if pred_pixel is not None:
                    pred_trail.append(pred_pixel)
                    for i in range(1, len(pred_trail)):
                        cv2.line(frame_bgr, pred_trail[i - 1], pred_trail[i], (0, 0, 255), 2)
                    cv2.circle(frame_bgr, pred_pixel, 15, (0, 0, 255), 3)
                    if current_pixel is not None:
                        cv2.line(frame_bgr, current_pixel, pred_pixel, (0, 0, 255), 2)
                    pred_label = f"x:{px:.2f} y:{py:.2f} z:{pz:.2f}m +{PREDICTION_HORIZON}s"
                    cv2.putText(
                        frame_bgr, pred_label,
                        (pred_pixel[0] + 20, pred_pixel[1]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
                    )

            if frame_idx in pred_buffer and kf.initialized and current_pixel is not None:
                epx, epy, epz = pred_buffer.pop(frame_idx)
                ax = float(kf.kf.statePost[0, 0])
                ay = float(kf.kf.statePost[1, 0])
                az = float(kf.kf.statePost[2, 0])
                error = float(np.linalg.norm([epx - ax, epy - ay, epz - az]))

                if error < 0.02:
                    acc_color = (0, 255, 0)
                elif error < 0.06:
                    acc_color = (0, 255, 255)
                else:
                    acc_color = (0, 0, 255)

                cv2.circle(frame_bgr, current_pixel, 25, acc_color, 4)
                cv2.putText(
                    frame_bgr, f"err:{error * 100:.1f}cm",
                    (current_pixel[0] + 20, current_pixel[1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, acc_color, 2,
                )

            writer.write(frame_bgr)

        frame_idx += 1

    t_pipeline_total = time.perf_counter() - t_pipeline_start

    if visualize:
        assert writer is not None
        assert output_path is not None
        writer.release()
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", tmp_path,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-an", output_path,
            ],
            check=True,
        )
        os.remove(tmp_path)

    cam.close()

    lat = np.array(latencies)
    metrics = {
        "latency_mean_ms": float(np.mean(lat)),
        "latency_p95_ms": float(np.percentile(lat, 95)),
        "latency_max_ms": float(np.max(lat)),
        "throughput_fps": frame_idx / t_pipeline_total,
        "ram_mean_mb": float(np.mean(ram_samples)),
        "ram_peak_mb": float(np.max(ram_samples)),
        "gpu_peak_mb": (
            torch.cuda.max_memory_allocated() / 1e6 if _TORCH_CUDA else None
        ),
    }

    return ground_truth, predictions, metrics


def compute_ade_fde(
    gt: dict,
    predictions: dict,
) -> tuple[list[int], list[float], list[float]]:
    """Compute ADE and FDE per prediction frame.

    ADE = mean Euclidean error across all PREDICTION_STEPS steps.
    FDE = Euclidean error at the final step only.
    Frames where any future GT position is missing are skipped.
    """
    frames, ade_list, fde_list = [], [], []
    for frame_idx, pred_sequence in predictions.items():
        step_errors = []
        for step, (px, py, pz) in enumerate(pred_sequence, 1):
            gt_xyz = gt.get(frame_idx + step)
            if gt_xyz is None:
                break
            gx, gy, gz = gt_xyz
            step_errors.append(float(np.linalg.norm([px - gx, py - gy, pz - gz])))

        if len(step_errors) == len(pred_sequence):
            frames.append(frame_idx)
            ade_list.append(float(np.mean(step_errors)))
            fde_list.append(step_errors[-1])

    return frames, ade_list, fde_list


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model = load_model("yolov8x.pt")

    ground_truth, predictions, metrics = run_pipeline(
        SVO_PATH,
        model,
        visualize=VISUALIZE,
        output_path=f"{OUTPUT_DIR}/output.mp4",
    )

    # Ground truth CSV
    with open(f"{OUTPUT_DIR}/ground_truth.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "x", "y", "z"])
        for frame_idx, (x, y, z) in ground_truth.items():
            writer.writerow([frame_idx, round(x, 3), round(y, 3), round(z, 3)])

    # Predictions CSV (one row per frame per step)
    with open(f"{OUTPUT_DIR}/predictions.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "step", "pred_x", "pred_y", "pred_z"])
        for frame_idx, pred_sequence in predictions.items():
            for step, (px, py, pz) in enumerate(pred_sequence, 1):
                writer.writerow([frame_idx, step, round(px, 3), round(py, 3), round(pz, 3)])

    frames, ade_list, fde_list = compute_ade_fde(ground_truth, predictions)

    # ADE / FDE plot
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    axes[0].plot(frames, ade_list, color="steelblue", linewidth=1)
    axes[0].axhline(np.mean(ade_list), color="red", linestyle="--",
                    label=f"mean {np.mean(ade_list):.3f} m")
    axes[0].set_ylabel("ADE (m)")
    axes[0].set_title("Average Displacement Error")
    axes[0].legend()

    axes[1].plot(frames, fde_list, color="darkorange", linewidth=1)
    axes[1].axhline(np.mean(fde_list), color="red", linestyle="--",
                    label=f"mean {np.mean(fde_list):.3f} m")
    axes[1].set_ylabel("FDE (m)")
    axes[1].set_xlabel("Frame")
    axes[1].set_title("Final Displacement Error")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/ade_fde_plot.png")
    plt.close()

    n = len(frames)
    print(f"\n{'='*40}")
    print(f"  Prediction Quality  (n={n} frames)")
    print(f"{'='*40}")
    print(f"  Mean ADE : {np.mean(ade_list):.3f} m")
    print(f"  Mean FDE : {np.mean(fde_list):.3f} m")
    print(f"  Max  ADE : {np.max(ade_list):.3f} m")
    print(f"  Max  FDE : {np.max(fde_list):.3f} m")

    print(f"\n{'='*40}")
    print(f"  System Performance")
    print(f"{'='*40}")
    print(f"  Latency mean  : {metrics['latency_mean_ms']:.1f} ms")
    print(f"  Latency p95   : {metrics['latency_p95_ms']:.1f} ms")
    print(f"  Latency max   : {metrics['latency_max_ms']:.1f} ms")
    print(f"  Throughput    : {metrics['throughput_fps']:.1f} FPS")
    print(f"  RAM mean      : {metrics['ram_mean_mb']:.0f} MB")
    print(f"  RAM peak      : {metrics['ram_peak_mb']:.0f} MB")
    if metrics["gpu_peak_mb"] is not None:
        print(f"  GPU peak VRAM : {metrics['gpu_peak_mb']:.0f} MB")
