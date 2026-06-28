import os
import time
import numpy as np
import psutil
import pyzed.sl as sl
from pipeline import (
    open_svo, get_intrinsics, grab_frame,
    load_model, detect_ball_bbox, calc_ball_3d_position,
    BallKalmanFilter, KFConfig,
)
from metrics import (
    reset_gpu_stats, compute_frame_metrics, compute_ade_fde,
    print_summary_table, write_results_csv, save_ade_fde_plot,
)
from visualizer import FrameVisualizer

SVO_PATHS = [
    "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-34-15.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_one_ball_straight_line_21-32-13.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-29.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-44.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-05.svo2",
    "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-18.svo2",
]
OUTPUT_DIR = "/app/output"
FPS = 30
PREDICTION_HORIZON = 0.2
PREDICTION_STEPS = round(PREDICTION_HORIZON * FPS)
MAX_MISSED = 5
VISUALIZE = True
PHASE = 2

_ZED_X = 0.008 ** 2
_ZED_Y = 0.011 ** 2
_ZED_Z = 0.008 ** 2

CONFIGS = [
    KFConfig(name=f"vpn_{vpn}",
             velocity_process_noise=vpn,
             measurement_noise_x=_ZED_X, measurement_noise_y=_ZED_Y, measurement_noise_z=_ZED_Z)
    for vpn in [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
]


def detect_and_update_filter(model, left_rgb, xyz_map, kf):
    """Detect ball and update KF. Returns (smoothed_xyz, raw_xyz) or (None, None)."""
    if kf.initialized:
        kf.predict()

    bbox_coordinates = detect_ball_bbox(model, left_rgb)
    if bbox_coordinates is None:
        return None, None

    raw_xyz = calc_ball_3d_position(xyz_map, *bbox_coordinates)
    if raw_xyz is None:
        return None, None

    x, y, z = raw_xyz
    if not kf.initialized:
        kf.reset(x, y, z)
        kf.predict()

    smoothed_xyz = kf.correct(x, y, z)
    return smoothed_xyz, raw_xyz


def run_pipeline(svo_path, yolo_model, config=None, visualizer=None):
    """Run the full pipeline on one SVO file. Returns (ground_truth, predictions, metrics)."""
    cam = open_svo(svo_path)
    mat_rgb, mat_xyz = sl.Mat(), sl.Mat()
    kf = BallKalmanFilter(dt=1 / FPS, config=config)

    ground_truth, predictions = {}, {}
    frame_index = missed = corrections = 0
    latencies, ram_samples = [], []
    process = psutil.Process()

    reset_gpu_stats()

    t_start = time.perf_counter()

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        t_frame = time.perf_counter()
        left_rgb, xyz_map = result

        smoothed_xyz, raw_xyz = detect_and_update_filter(yolo_model, left_rgb, xyz_map, kf)

        if raw_xyz is not None:
            ground_truth[frame_index] = raw_xyz
            missed = 0
            corrections += 1
        else:
            missed += 1

        pred_sequence = None
        if corrections >= 2 and missed < MAX_MISSED:
            pred_sequence = [kf.predict_ahead(s / FPS) for s in range(1, PREDICTION_STEPS + 1)]
            predictions[frame_index] = pred_sequence

        latencies.append((time.perf_counter() - t_frame) * 1000)
        ram_samples.append(process.memory_info().rss / 1e6)

        if visualizer is not None:
            visualizer.draw_frame(left_rgb, smoothed_xyz, kf, pred_sequence, missed)

        frame_index += 1

    total_time = time.perf_counter() - t_start
    if visualizer is not None:
        visualizer.release()
    cam.close()

    return ground_truth, predictions, compute_frame_metrics(latencies, ram_samples, frame_index, total_time)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yolo_model = load_model("yolov8x.pt")

    seq_names = [os.path.splitext(os.path.basename(p))[0] for p in SVO_PATHS]
    per_seq_rows: list[dict] = []
    sweep_results: list[dict] = []

    for cfg in CONFIGS:
        cfg_ade_all, cfg_fde_all, cfg_latencies, cfg_fps = [], [], [], []

        for svo_path, seq_name in zip(SVO_PATHS, seq_names):
            print(f"Running: {cfg.name}  |  {seq_name} ...")
            gt, preds, metrics = run_pipeline(svo_path, yolo_model, config=cfg)
            frames, ade_list, fde_list = compute_ade_fde(gt, preds)

            cfg_ade_all.extend(ade_list)
            cfg_fde_all.extend(fde_list)
            cfg_latencies.append(metrics["latency_p95_ms"])
            cfg_fps.append(metrics["throughput_fps"])

            per_seq_rows.append({
                "config":               cfg.name,
                "velocity_process_noise": cfg.velocity_process_noise,
                "position_process_noise": cfg.position_process_noise,
                "measurement_noise_x":    cfg.measurement_noise_x,
                "measurement_noise_y":    cfg.measurement_noise_y,
                "measurement_noise_z":    cfg.measurement_noise_z,
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
            "config":  cfg,
            "ade_all": cfg_ade_all,
            "fde_all": cfg_fde_all,
            "lat_p95": float(np.mean(cfg_latencies)),
            "fps":     float(np.mean(cfg_fps)),
        })

    print_summary_table(sweep_results, len(SVO_PATHS))
    write_results_csv(per_seq_rows, f"{OUTPUT_DIR}/sweep_phase_{PHASE}.csv")
    save_ade_fde_plot(sweep_results, len(SVO_PATHS), f"{OUTPUT_DIR}/ade_fde_phase_{PHASE}.png")

    if VISUALIZE:
        best = min(sweep_results, key=lambda r: np.mean(r["fde_all"]))
        print(f"\nVisualising best config ({best['config'].name}) on: {seq_names[0]}")
        cam = open_svo(SVO_PATHS[0])
        vis = FrameVisualizer(
            f"{OUTPUT_DIR}/output.mp4",
            intrinsics=get_intrinsics(cam),
        )
        cam.close()
        run_pipeline(SVO_PATHS[0], yolo_model, config=best["config"], visualizer=vis)
