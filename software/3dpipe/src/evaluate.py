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
    project_to_pixel, BallKalmanFilter, KFConfig,
)

try:
    import torch
    _TORCH_CUDA = torch.cuda.is_available()
except ImportError:
    _TORCH_CUDA = False

SVO_PATHS = [
    "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-34-15.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-29.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-29.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-44.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-05.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-18.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_ball_behind_box_21-40-04.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_ball_roll_21-53-17.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_ball_up_a_ramp_21-46-08.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_ball_up_a_ramp_and_back_21-45-51.svo2",
]
OUTPUT_DIR = "/app/output"
FPS = 30
PREDICTION_HORIZON = 0.2
PREDICTION_STEPS = round(PREDICTION_HORIZON * FPS)  # 6
MAX_MISSED = 5
VISUALIZE = True

# ZED per-axis variance from static analysis (std: X=0.8cm, Y=1.1cm, Z=0.8cm)
_ZED_X = 0.008 ** 2   # 0.000064
_ZED_Y = 0.011 ** 2   # 0.000121
_ZED_Z = 0.008 ** 2   # 0.000064

CONFIGS = [
    KFConfig(name="baseline",
             vel_process_noise=0.01,
             meas_noise_x=0.001, meas_noise_y=0.001, meas_noise_z=0.001),
    KFConfig(name="zed_noise",
             vel_process_noise=0.01,
             meas_noise_x=_ZED_X, meas_noise_y=_ZED_Y, meas_noise_z=_ZED_Z),
    KFConfig(name="high_vel",
             vel_process_noise=0.1,
             meas_noise_x=0.001, meas_noise_y=0.001, meas_noise_z=0.001),
    KFConfig(name="zed_noise_high_vel",
             vel_process_noise=0.1,
             meas_noise_x=_ZED_X, meas_noise_y=_ZED_Y, meas_noise_z=_ZED_Z),
]


def run_pipeline(
    svo_path: str,
    model,
    config: KFConfig | None = None,
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
    kf = BallKalmanFilter(dt=1 / FPS, config=config)

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

    # seq_name: just the filename without extension, used for labelling
    seq_names = [os.path.splitext(os.path.basename(p))[0] for p in SVO_PATHS]

    # per_seq_rows: one entry per (config, sequence) for the detailed CSV
    per_seq_rows: list[dict] = []

    # sweep_results: one entry per config, holding aggregated stats across all sequences
    sweep_results: list[dict] = []

    for cfg in CONFIGS:
        cfg_ade_all: list[float] = []
        cfg_fde_all: list[float] = []
        cfg_latencies: list[float] = []
        cfg_fps: list[float] = []

        for svo_path, seq_name in zip(SVO_PATHS, seq_names):
            print(f"Running: {cfg.name}  |  {seq_name} ...")
            gt, preds, metrics = run_pipeline(svo_path, model, config=cfg, visualize=False)
            frames, ade_list, fde_list = compute_ade_fde(gt, preds)

            cfg_ade_all.extend(ade_list)
            cfg_fde_all.extend(fde_list)
            cfg_latencies.append(metrics["latency_p95_ms"])
            cfg_fps.append(metrics["throughput_fps"])

            per_seq_rows.append({
                "config":          cfg.name,
                "sequence":        seq_name,
                "n":               len(frames),
                "mean_ade_m":      round(float(np.mean(ade_list)), 4) if ade_list else None,
                "mean_fde_m":      round(float(np.mean(fde_list)), 4) if fde_list else None,
                "max_ade_m":       round(float(np.max(ade_list)),  4) if ade_list else None,
                "max_fde_m":       round(float(np.max(fde_list)),  4) if fde_list else None,
                "latency_mean_ms": round(metrics["latency_mean_ms"], 2),
                "latency_p95_ms":  round(metrics["latency_p95_ms"],  2),
                "latency_max_ms":  round(metrics["latency_max_ms"],  2),
                "throughput_fps":  round(metrics["throughput_fps"],  2),
                "ram_peak_mb":     round(metrics["ram_peak_mb"], 1),
                "gpu_peak_mb":     round(metrics["gpu_peak_mb"], 1) if metrics["gpu_peak_mb"] else None,
            })

        sweep_results.append({
            "config":    cfg,
            "ade_all":   cfg_ade_all,
            "fde_all":   cfg_fde_all,
            "lat_p95":   float(np.mean(cfg_latencies)),
            "fps":       float(np.mean(cfg_fps)),
        })

    # --- Comparison table (aggregated across all sequences) ---
    col = 22
    n_seqs = len(SVO_PATHS)
    header = (f"{'Config':<{col}} {'n':>5} {'ADE mean':>9} {'FDE mean':>9} "
              f"{'ADE max':>9} {'FDE max':>9} {'Lat p95':>9} {'FPS':>6}")
    print(f"\n{'='*len(header)}")
    print(f"  {n_seqs} sequence(s) - overall summary")
    print(f"{'='*len(header)}")
    print(header)
    print("-" * len(header))
    for r in sweep_results:
        ade, fde = r["ade_all"], r["fde_all"]
        print(f"{r['config'].name:<{col}} {len(ade):>5} "
              f"{np.mean(ade):>8.3f}m {np.mean(fde):>8.3f}m "
              f"{np.max(ade):>8.3f}m {np.max(fde):>8.3f}m "
              f"{r['lat_p95']:>8.1f}ms {r['fps']:>5.1f}")

    # --- Per-sequence detail table ---
    if n_seqs > 1:
        print(f"\n--- Per-sequence detail ---")
        seq_col = max(len(s) for s in seq_names) + 2
        for r in per_seq_rows:
            ade = r["mean_ade_m"] or 0
            fde = r["mean_fde_m"] or 0
            print(f"  {r['config']:<{col}} {r['sequence']:<{seq_col}} "
                  f"ADE {ade:.3f}m  FDE {fde:.3f}m")

    # --- Detailed CSV (one row per config × sequence) ---
    with open(f"{OUTPUT_DIR}/sweep_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(per_seq_rows[0].keys()))
        for row in per_seq_rows:
            w.writerow(list(row.values()))

    # --- ADE / FDE comparison plot (means across all sequences) ---
    config_names = [r["config"].name for r in sweep_results]
    mean_ades = [np.mean(r["ade_all"]) for r in sweep_results]
    mean_fdes = [np.mean(r["fde_all"]) for r in sweep_results]

    x = np.arange(len(config_names))
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(x, mean_ades, color="steelblue")
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(config_names, rotation=15, ha="right")
    axes[0].set_ylabel("ADE (m)")
    axes[0].set_title(f"Mean ADE across {n_seqs} sequence(s)")

    axes[1].bar(x, mean_fdes, color="darkorange")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(config_names, rotation=15, ha="right")
    axes[1].set_ylabel("FDE (m)")
    axes[1].set_title(f"Mean FDE across {n_seqs} sequence(s)")

    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/ade_fde_plot.png")
    plt.close()

    # --- Visualise best config on first sequence ---
    if VISUALIZE:
        best = min(sweep_results, key=lambda r: np.mean(r["fde_all"]))
        print(f"\nVisualising best config ({best['config'].name}) on: {seq_names[0]}")
        run_pipeline(
            SVO_PATHS[0], model,
            config=best["config"],
            visualize=True,
            output_path=f"{OUTPUT_DIR}/output.mp4",
        )
