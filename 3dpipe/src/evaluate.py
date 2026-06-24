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
    # "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-29.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-34-44.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-05.svo2",
    # "/datasets/Dataset_2/Clean/HD1080_one_ball_diagonal_21-35-18.svo2",
]
OUTPUT_DIR = "/app/output"
FPS = 30
PREDICTION_HORIZON = 0.2
PREDICTION_STEPS = round(PREDICTION_HORIZON * FPS)
MAX_MISSED = 5
VISUALIZE = True

_ZED_X = 0.008 ** 2
_ZED_Y = 0.011 ** 2
_ZED_Z = 0.008 ** 2

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


class FrameVisualizer:
    """Renders tracking and prediction overlays onto video frames."""

    def __init__(self, output_path: str, intrinsics: tuple[float, float, float, float]):
        self.output_path = output_path
        self.fx, self.fy, self.cx, self.cy = intrinsics
        self.trail: deque = deque()
        self.pred_trail: deque = deque()
        self._tmp_path = output_path + ".tmp.mp4"
        self._writer = cv2.VideoWriter(
            self._tmp_path,
            cv2.VideoWriter.fourcc(*"mp4v"),
            FPS,
            (1920, 1080),
        )

    def draw_frame(
        self,
        frame_rgb: np.ndarray,
        current_xyz: tuple[float, float, float] | None,
        kf_label_xyz: tuple[float, float, float] | None,
        pred_sequence: list[tuple[float, float, float]] | None,
        detected: bool,
    ) -> None:
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        current_pixel = None
        if current_xyz is not None:
            current_pixel = project_to_pixel(
                *current_xyz, self.fx, self.fy, self.cx, self.cy,
            )

        if current_pixel is not None:
            self.trail.append(current_pixel)

        self._draw_trail(frame_bgr)
        self._draw_current(frame_bgr, current_pixel, kf_label_xyz, detected)
        self._draw_prediction(frame_bgr, current_pixel, pred_sequence)
        self._writer.write(frame_bgr)

    def _draw_trail(self, frame_bgr: np.ndarray) -> None:
        for i in range(1, len(self.trail)):
            cv2.line(frame_bgr, self.trail[i - 1], self.trail[i], (0, 255, 0), 2)

    def _draw_current(
        self,
        frame_bgr: np.ndarray,
        pixel: tuple[int, int] | None,
        label_xyz: tuple[float, float, float] | None,
        detected: bool,
    ) -> None:
        if pixel is None:
            return
        color = (0, 255, 0) if detected else (0, 165, 255)
        cv2.circle(frame_bgr, pixel, 15, color, 3)
        if label_xyz is not None:
            lx, ly, lz = label_xyz
            cv2.putText(
                frame_bgr, f"x:{lx:.2f} y:{ly:.2f} z:{lz:.2f}m",
                (pixel[0] + 20, pixel[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2,
            )

    def _draw_prediction(
        self,
        frame_bgr: np.ndarray,
        current_pixel: tuple[int, int] | None,
        pred_sequence: list[tuple[float, float, float]] | None,
    ) -> None:
        if pred_sequence is None:
            return
        px, py, pz = pred_sequence[-1]
        pred_pixel = project_to_pixel(px, py, pz, self.fx, self.fy, self.cx, self.cy)
        if pred_pixel is None:
            return
        self.pred_trail.append(pred_pixel)
        for i in range(1, len(self.pred_trail)):
            cv2.line(frame_bgr, self.pred_trail[i - 1], self.pred_trail[i], (0, 0, 255), 2)
        cv2.circle(frame_bgr, pred_pixel, 15, (0, 0, 255), 3)
        if current_pixel is not None:
            cv2.line(frame_bgr, current_pixel, pred_pixel, (0, 0, 255), 2)
        cv2.putText(
            frame_bgr, f"x:{px:.2f} y:{py:.2f} z:{pz:.2f}m +{PREDICTION_HORIZON}s",
            (pred_pixel[0] + 20, pred_pixel[1]),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2,
        )

    def release(self) -> None:
        self._writer.release()
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", self._tmp_path,
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                "-an", self.output_path,
            ],
            check=True,
        )
        os.remove(self._tmp_path)


def _process_frame(
    model, left_rgb: np.ndarray, xyz_map: np.ndarray,
    kf: BallKalmanFilter, missed: int, corrections: int,
) -> tuple[
    tuple[float, float, float] | None,
    tuple[float, float, float] | None,
    int, int,
]:
    """Detect ball, update KF. Returns (smoothed_xyz, raw_xyz, missed, corrections)."""
    if kf.initialized:
        kf.predict()

    bbox = detect_ball_bbox(model, left_rgb)
    smoothed_xyz = None
    raw_xyz = None

    if bbox is not None:
        raw_xyz = calc_ball_3d_position(xyz_map, *bbox)
        if raw_xyz is not None:
            x, y, z = raw_xyz
            if not kf.initialized:
                kf.reset(x, y, z)
                kf.predict()
            smoothed_xyz = kf.correct(x, y, z)
            return smoothed_xyz, raw_xyz, 0, corrections + 1

    return smoothed_xyz, raw_xyz, missed + 1, corrections


def _kf_display_state(
    kf: BallKalmanFilter, smoothed_xyz: tuple[float, float, float] | None, missed: int,
) -> tuple[tuple[float, float, float] | None, tuple[float, float, float] | None]:
    """Returns (current_xyz, label_xyz) for visualization from the KF state."""
    if not kf.initialized:
        return None, None

    state_xyz = (
        float(kf.kf.statePost[0, 0]),
        float(kf.kf.statePost[1, 0]),
        float(kf.kf.statePost[2, 0]),
    )

    if smoothed_xyz is not None:
        return smoothed_xyz, state_xyz
    if 0 < missed < MAX_MISSED:
        return state_xyz, state_xyz
    return None, state_xyz


def _compute_metrics(
    latencies: list[float], ram_samples: list[float],
    frame_count: int, total_time: float,
) -> dict:
    lat = np.array(latencies)
    return {
        "latency_mean_ms": float(np.mean(lat)),
        "latency_p95_ms": float(np.percentile(lat, 95)),
        "latency_max_ms": float(np.max(lat)),
        "throughput_fps": frame_count / total_time,
        "ram_mean_mb": float(np.mean(ram_samples)),
        "ram_peak_mb": float(np.max(ram_samples)),
        "gpu_peak_mb": (
            torch.cuda.max_memory_allocated() / 1e6 if _TORCH_CUDA else None  # type: ignore[possibly-undefined]
        ),
    }


def run_pipeline(
    svo_path: str,
    model,
    config: KFConfig | None = None,
    visualizer: FrameVisualizer | None = None,
) -> tuple[dict, dict, dict]:
    """Run the full pipeline on one SVO file.

    Returns (ground_truth, predictions, metrics).
    """
    cam = open_svo(svo_path)
    mat_rgb, mat_xyz = sl.Mat(), sl.Mat()
    kf = BallKalmanFilter(dt=1 / FPS, config=config)

    ground_truth: dict = {}
    predictions: dict = {}
    frame_idx = 0
    missed = 0
    corrections = 0

    latencies: list[float] = []
    process = psutil.Process()
    ram_samples: list[float] = []

    if _TORCH_CUDA:
        torch.cuda.reset_peak_memory_stats()  # type: ignore[possibly-undefined]

    t_start = time.perf_counter()

    while True:
        result = grab_frame(cam, mat_rgb, mat_xyz)
        if result is None:
            break

        t_frame = time.perf_counter()
        left_rgb, xyz_map = result

        smoothed_xyz, raw_xyz, missed, corrections = _process_frame(
            model, left_rgb, xyz_map, kf, missed, corrections,
        )
        if raw_xyz is not None:
            ground_truth[frame_idx] = raw_xyz

        pred_sequence = None
        if corrections >= 2 and missed < MAX_MISSED:
            pred_sequence = [kf.predict_ahead(s / FPS) for s in range(1, PREDICTION_STEPS + 1)]
            predictions[frame_idx] = pred_sequence

        latencies.append((time.perf_counter() - t_frame) * 1000)
        ram_samples.append(process.memory_info().rss / 1e6)

        if visualizer is not None:
            current_xyz, label_xyz = _kf_display_state(kf, smoothed_xyz, missed)
            visualizer.draw_frame(left_rgb, current_xyz, label_xyz, pred_sequence, detected=(missed == 0))

        frame_idx += 1

    total_time = time.perf_counter() - t_start
    if visualizer is not None:
        visualizer.release()
    cam.close()

    return ground_truth, predictions, _compute_metrics(latencies, ram_samples, frame_idx, total_time)


def compute_ade_fde(
    gt: dict,
    predictions: dict,
) -> tuple[list[int], list[float], list[float]]:
    """ADE = mean error across all steps. FDE = error at the final step."""
    frames, ade_list, fde_list = [], [], []
    for frame_idx, pred_sequence in predictions.items():
        step_errors = []
        for step, (p_x, p_y, p_z) in enumerate(pred_sequence, 1):
            gt_xyz = gt.get(frame_idx + step)
            if gt_xyz is None:
                break
            gt_x, gt_y, gt_z = gt_xyz
            step_errors.append(float(np.linalg.norm([p_x - gt_x, p_y - gt_y, p_z - gt_z])))

        if len(step_errors) == len(pred_sequence):
            frames.append(frame_idx)
            ade_list.append(float(np.mean(step_errors)))
            fde_list.append(step_errors[-1])

    return frames, ade_list, fde_list


def print_summary_table(sweep_results: list[dict], n_seqs: int) -> None:
    col = 22
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


def write_results_csv(per_seq_rows: list[dict], path: str) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(list(per_seq_rows[0].keys()))
        for row in per_seq_rows:
            w.writerow(list(row.values()))


def save_ade_fde_plot(sweep_results: list[dict], n_seqs: int, path: str) -> None:
    config_names = [r["config"].name for r in sweep_results]
    mean_ades = [np.mean(r["ade_all"]) for r in sweep_results]
    mean_fdes = [np.mean(r["fde_all"]) for r in sweep_results]

    x = np.arange(len(config_names))
    _, axes = plt.subplots(1, 2, figsize=(12, 5))

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
    plt.savefig(path)
    plt.close()


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model = load_model("yolov8x.pt")

    seq_names = [os.path.splitext(os.path.basename(p))[0] for p in SVO_PATHS]
    per_seq_rows: list[dict] = []
    sweep_results: list[dict] = []

    for cfg in CONFIGS:
        cfg_ade_all: list[float] = []
        cfg_fde_all: list[float] = []
        cfg_latencies: list[float] = []
        cfg_fps: list[float] = []

        for svo_path, seq_name in zip(SVO_PATHS, seq_names):
            print(f"Running: {cfg.name}  |  {seq_name} ...")
            gt, preds, metrics = run_pipeline(svo_path, model, config=cfg)
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

    print_summary_table(sweep_results, len(SVO_PATHS))
    write_results_csv(per_seq_rows, f"{OUTPUT_DIR}/sweep_results.csv")
    save_ade_fde_plot(sweep_results, len(SVO_PATHS), f"{OUTPUT_DIR}/ade_fde_plot.png")

    if VISUALIZE:
        best = min(sweep_results, key=lambda r: np.mean(r["fde_all"]))
        print(f"\nVisualising best config ({best['config'].name}) on: {seq_names[0]}")
        vis = FrameVisualizer(
            f"{OUTPUT_DIR}/output.mp4",
            intrinsics=get_intrinsics(open_svo(SVO_PATHS[0])),
        )
        run_pipeline(SVO_PATHS[0], model, config=best["config"], visualizer=vis)
