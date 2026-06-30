"""Generate presentation-ready plots and tables from experiment results."""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUTPUT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.dirname(OUTPUT_DIR)

PHASE_1_CSV = os.path.join(DATA_DIR, "sweep_phase_1.csv")
PHASE_4_CSV = os.path.join(DATA_DIR, "sweep_phase_4.csv")

DPI = 200
FONT_SIZE = 13
TITLE_SIZE = 15
BAR_LABEL_SIZE = 11

plt.rcParams.update({
    "font.size": FONT_SIZE,
    "axes.titlesize": TITLE_SIZE,
    "axes.labelsize": FONT_SIZE,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def render_table(columns, rows, col_widths, title, out_path):
    """Render a table as a clean image."""
    n_cols = len(columns)
    n_rows = len(rows)
    fig_w = sum(col_widths) + 0.4
    fig_h = 0.55 * (n_rows + 1) + 0.7

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")
    fig.suptitle(title, fontsize=TITLE_SIZE, fontweight="bold", y=0.95)

    table = ax.table(
        cellText=rows,
        colLabels=columns,
        cellLoc="center",
        loc="center",
        colWidths=[w / fig_w for w in col_widths],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(FONT_SIZE)
    table.scale(1, 1.8)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cccccc")
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_facecolor("#4472C4")
            cell.set_text_props(color="white", fontweight="bold")
        elif row % 2 == 0:
            cell.set_facecolor("#f0f4fa")
        else:
            cell.set_facecolor("white")

    plt.savefig(out_path, dpi=DPI, bbox_inches="tight", pad_inches=0.15)
    plt.close()
    print(f"Saved: {out_path}")


def plot_detection_accuracy():
    """Table with combined 3D detection error and detection rate."""
    columns = ["Metric", "Value"]
    rows = [
        ["Detection rate", "41 / 45  (91%)"],
        ["Combined 3D error (mean)", "6.7 cm"],
        ["Combined 3D error (std)", "0.9 cm"],
        ["Test positions", "45  (3 depths x 15 lateral)"],
    ]
    render_table(columns, rows, [3.5, 3.5], "Detection Accuracy",
                 os.path.join(OUTPUT_DIR, "detection_accuracy.png"))


def plot_phase1_sweep():
    """Phase 1: velocity process noise sweep - ADE and FDE bar charts."""
    df = pd.read_csv(PHASE_1_CSV)

    configs = df["config"].unique()
    mean_ades, mean_fdes = [], []
    labels = []

    for cfg in configs:
        sub = df[df["config"] == cfg]
        ade_vals = sub["mean_ade_m"].dropna()
        fde_vals = sub["mean_fde_m"].dropna()
        mean_ades.append(ade_vals.mean() * 100)
        mean_fdes.append(fde_vals.mean() * 100)
        vpn = sub["velocity_process_noise"].iloc[0]
        labels.append(str(vpn))

    n_seqs = df.groupby("config")["sequence"].nunique().iloc[0]
    x = np.arange(len(labels))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(f"Velocity process noise sweep  ({n_seqs} sequences)",
                 fontsize=TITLE_SIZE, fontweight="bold")

    bars1 = ax1.bar(x, mean_ades, color="#4472C4", width=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.set_xlabel("Velocity process noise ($q_v$)")
    ax1.set_ylabel("Mean ADE (cm)")
    ax1.set_ylim(0, max(mean_ades) * 1.25)
    ax1.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars1, mean_ades):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f"{val:.2f}", ha="center", va="bottom", fontsize=BAR_LABEL_SIZE)

    bars2 = ax2.bar(x, mean_fdes, color="#ED7D31", width=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels)
    ax2.set_xlabel("Velocity process noise ($q_v$)")
    ax2.set_ylabel("Mean FDE (cm)")
    ax2.set_ylim(0, max(mean_fdes) * 1.25)
    ax2.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars2, mean_fdes):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f"{val:.2f}", ha="center", va="bottom", fontsize=BAR_LABEL_SIZE)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(OUTPUT_DIR, "phase1_vpn_sweep.png")
    plt.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")

    best_idx = int(np.argmin(mean_ades))
    columns = ["$q_v$", "Mean ADE (cm)", "Mean FDE (cm)"]
    rows = []
    for i in range(len(labels)):
        marker = " *" if i == best_idx else ""
        rows.append([labels[i], f"{mean_ades[i]:.2f}{marker}", f"{mean_fdes[i]:.2f}{marker}"])
    render_table(columns, rows, [1.8, 2.5, 2.5],
                 "Phase 1: velocity process noise sweep",
                 os.path.join(OUTPUT_DIR, "phase1_vpn_table.png"))


def plot_phase4_cv_vs_ca():
    """Phase 4: constant-velocity vs constant-acceleration model."""
    df = pd.read_csv(PHASE_4_CSV)

    configs = df["config"].unique()
    mean_ades, mean_fdes = [], []
    labels = []

    for cfg in configs:
        sub = df[df["config"] == cfg]
        mean_ades.append(sub["mean_ade_m"].dropna().mean() * 100)
        mean_fdes.append(sub["mean_fde_m"].dropna().mean() * 100)
        if cfg == "cv_optimized":
            labels.append("CV (baseline)")
        else:
            apn = sub["acceleration_process_noise"].iloc[0]
            labels.append(f"CA  $q_a$={apn}")

    n_seqs = df.groupby("config")["sequence"].nunique().iloc[0]
    x = np.arange(len(labels))

    colors = ["#4472C4"] + ["#A9D18E"] * (len(labels) - 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))
    fig.suptitle(f"Constant-velocity vs constant-acceleration  ({n_seqs} sequence)",
                 fontsize=TITLE_SIZE, fontweight="bold")

    bars1 = ax1.bar(x, mean_ades, color=colors, width=0.6)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=20, ha="right")
    ax1.set_ylabel("Mean ADE (cm)")
    ax1.set_ylim(0, max(mean_ades) * 1.3)
    ax1.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars1, mean_ades):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                 f"{val:.2f}", ha="center", va="bottom", fontsize=BAR_LABEL_SIZE)

    bars2 = ax2.bar(x, mean_fdes, color=colors, width=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=20, ha="right")
    ax2.set_ylabel("Mean FDE (cm)")
    ax2.set_ylim(0, max(mean_fdes) * 1.3)
    ax2.grid(axis="y", alpha=0.3)
    for bar, val in zip(bars2, mean_fdes):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                 f"{val:.2f}", ha="center", va="bottom", fontsize=BAR_LABEL_SIZE)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(OUTPUT_DIR, "phase4_cv_vs_ca.png")
    plt.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close()
    print(f"Saved: {out}")


def plot_system_performance():
    """System performance table from phase 1 best config."""
    df = pd.read_csv(PHASE_1_CSV)
    best_cfg = "vpn_0.02"
    sub = df[df["config"] == best_cfg]

    lat_p95 = sub["latency_p95_ms"].mean()
    fps = sub["throughput_fps"].mean()
    ram = sub["ram_peak_mb"].max()
    gpu = sub["gpu_peak_mb"].max()

    columns = ["Metric", "Value"]
    rows = [
        ["Latency (p95)", f"{lat_p95:.1f} ms"],
        ["Throughput", f"{fps:.1f} fps"],
        ["Camera rate", "30 fps"],
        ["RAM peak", f"{ram / 1000:.1f} GB"],
        ["GPU memory peak", f"{gpu / 1000:.1f} GB"],
    ]
    render_table(columns, rows, [3.0, 2.5], "System Performance",
                 os.path.join(OUTPUT_DIR, "system_performance.png"))


def plot_prediction_summary():
    """Compare best CV vs best CA on the same sequence (phase 4 data)."""
    df = pd.read_csv(PHASE_4_CSV)

    cv = df[df["config"] == "cv_optimized"].iloc[0]
    ca = df[df["config"] == "ca_apn_0.01"].iloc[0]

    columns = ["Metric", "Best CV ($q_v$ = 0.02)", "Best CA ($q_a$ = 0.01)"]
    rows = [
        ["Mean ADE", f"{cv['mean_ade_m']*100:.2f} cm", f"{ca['mean_ade_m']*100:.2f} cm"],
        ["Mean FDE", f"{cv['mean_fde_m']*100:.2f} cm", f"{ca['mean_fde_m']*100:.2f} cm"],
        ["Max ADE",  f"{cv['max_ade_m']*100:.2f} cm",  f"{ca['max_ade_m']*100:.2f} cm"],
        ["Max FDE",  f"{cv['max_fde_m']*100:.2f} cm",  f"{ca['max_fde_m']*100:.2f} cm"],
        ["Prediction horizon", "0.2 s (6 frames)", ""],
    ]
    render_table(columns, rows, [2.8, 3.2, 3.2],
                 "Prediction: CV vs CA",
                 os.path.join(OUTPUT_DIR, "prediction_summary.png"))


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plot_detection_accuracy()
    plot_phase1_sweep()
    plot_phase4_cv_vs_ca()
    plot_system_performance()
    plot_prediction_summary()
    print(f"\nAll outputs saved to: {OUTPUT_DIR}")
