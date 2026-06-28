import csv
import numpy as np
import matplotlib.pyplot as plt

try:
    import torch
    _TORCH_CUDA = torch.cuda.is_available()
except ImportError:
    _TORCH_CUDA = False


def reset_gpu_stats() -> None:
    if _TORCH_CUDA:
        torch.cuda.reset_peak_memory_stats()  # type: ignore[possibly-undefined]


def compute_frame_metrics(
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


def compute_ade_fde(
    gt: dict, predictions: dict,
) -> tuple[list[int], list[float], list[float]]:
    """ADE = mean error across all steps. FDE = error at the final step."""
    frames, ade_list, fde_list = [], [], []
    for frame_index, pred_sequence in predictions.items():
        step_errors = []
        for step, (p_x, p_y, p_z) in enumerate(pred_sequence, 1):
            gt_xyz = gt.get(frame_index + step)
            if gt_xyz is None:
                break
            gt_x, gt_y, gt_z = gt_xyz
            step_errors.append(float(np.linalg.norm([p_x - gt_x, p_y - gt_y, p_z - gt_z])))

        if len(step_errors) == len(pred_sequence):
            frames.append(frame_index)
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
