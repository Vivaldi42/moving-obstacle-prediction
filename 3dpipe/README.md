# 3D Obstacle Prediction Pipeline

Real-time 3D ball tracking and short-horizon trajectory prediction using a ZED 2i stereo camera, YOLOv8x object detection, and a Kalman filter. Evaluates both a constant-velocity (CV) and a constant-acceleration (CA) motion model across recorded SVO2 sequences.

## Prerequisites

- Docker with the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- An NVIDIA GPU (tested on RTX 4090; Jetson Orin also supported)
- ZED SDK installed on the host (required for SVO2 playback)
- SVO2 recordings placed in `/data/ZED` (see [Datasets](#datasets))
- `yolov8x.pt` weights file in the repo root (see [YOLO weights](#yolo-weights))

## Datasets

SVO2 recordings are stored at `/data/ZED` and shared between users. The Docker container mounts that directory at `/datasets`. To use a different path:

```bash
export ZED_DATASET_PATH=/your/path/to/ZED
docker compose up perception-x86
```

To add a new recording, copy the `.svo2` file into `/data/ZED/Dataset_2/Clean/` and add its path to `SVO_PATHS` in [src/evaluate.py](src/evaluate.py).

## YOLO weights

`yolov8x.pt` is not tracked in git. Download it once and place it at the repo root:

```bash
pip install ultralytics
python -c "from ultralytics import YOLO; YOLO('yolov8x.pt')"
```

The file is picked up automatically by the Docker mount (`.:/app`).

## Build

```bash
# x86 workstation
docker build -f docker/Dockerfile.x86 -t perception:x86 .

# Jetson
docker build -f docker/Dockerfile.jetson -t perception:jetson .
```

> **Jetson - verify the base image before building.**
> `docker/Dockerfile.jetson` uses `stereolabs/zed:5.2-devel-l4t-r36.4`, which may not have been published by Stereolabs.
> The x86 image is on ZED SDK 5.2.2; the Jetson image has never been verified to build successfully.
> Check available Jetson tags at [hub.docker.com/r/stereolabs/zed/tags](https://hub.docker.com/r/stereolabs/zed/tags)
> and update `docker/Dockerfile.jetson` line 1 to a tag that exists before attempting a Jetson build.

## Run

The default command is `python src/evaluate.py`. To run a different script, set `PYTHON_COMMAND`:

```bash
# x86 workstation
docker compose up perception-x86

# Jetson
docker compose up perception-jetson

# Convert a single SVO2 to MP4 instead of running the full evaluation
PYTHON_COMMAND="python src/svo2_to_mp4.py /datasets/my_recording.svo2 /app/output/my_recording.mp4" docker compose up perception-x86

# Open an interactive shell (useful for running scripts manually or debugging)
PYTHON_COMMAND="bash" docker compose run --rm perception-x86
```

Output files are written to `output/` in the repo root.

## Configuration

All tunable constants are at the top of [src/evaluate.py](src/evaluate.py):

| Variable | Default | Description |
|---|---|---|
| `SVO_PATHS` | list of 10 sequences | SVO2 files to evaluate |
| `PHASE` | `4` | Phase label used in output filenames |
| `VISUALIZE` | `True` | Whether to render and save an annotated MP4 |
| `CONFIGS` | CV + 5 CA variants | Kalman filter configurations to sweep |

## Outputs

After a run, `output/` contains:

| File | Description |
|---|---|
| `sweep_phase_N.csv` | Per-sequence metrics for every config |
| `ade_fde_phase_N.png` | ADE/FDE bar chart comparing configs |
| `output.mp4` | Annotated video for the best-performing config |
| `ground_truth.csv` | Raw 3D positions from the last sequence |
| `predictions.csv` | Predicted positions from the last sequence |

## Project structure

```
src/
  pipeline.py       - ZED I/O, YOLO detection, CV and CA Kalman filter
  evaluate.py       - Entry point: sweeps configs across sequences, writes results
  metrics.py        - ADE/FDE, latency, throughput, memory metrics
  visualizer.py     - Overlay renderer, ffmpeg MP4 writer
  svo2_to_mp4.py    - Utility: convert SVO2 to plain MP4
docker/
  Dockerfile.x86
  Dockerfile.jetson
docs/
  project_report/   - Full project report
  system_design/    - Architecture and design decisions
  kalman_filter/    - Kalman filter derivation and configuration
  benchmarks/       - Evaluation metrics definition
  detection_accuracy/ - Detection accuracy experiment
notebooks/
  kf_sweep.ipynb    - Interactive Kalman filter parameter exploration
```

## Documentation

**Start here:** [docs/project_report/project_report.md](docs/project_report/project_report.md) - full project report covering motivation, research questions, evaluation methodology, results across all four phases, and conclusions. Includes the Phase 4 CV vs CA comparison with final ADE/FDE numbers.

**Implementation details:** [docs/system_design/system_design.md](docs/system_design/system_design.md) - covers every design decision in the pipeline: camera setup, YOLO detection configuration, front-face depth sampling, the CV and CA Kalman filter formulations (state vectors, transition matrices, process and measurement noise), prediction, coasting behaviour, and the overlay renderer. Also documents the configuration sweep structure and output files.

**Architecture diagram:** [docs/system_design/architecture.md](docs/system_design/architecture.md) - Mermaid flowchart of the full data path from SVO2 input through detection, depth estimation, Kalman filtering, and output (annotated MP4, CSV files, ADE/FDE plot).

**Kalman filter derivation:** [docs/kalman_filter/kalman_filter.md](docs/kalman_filter/kalman_filter.md) - step-by-step derivation of the CV and CA filter variants, state vector definitions, process and measurement noise matrices, forward prediction formulas, and a summary of results across all evaluated configurations.

**Evaluation metrics:** [docs/benchmarks/benchmarks.md](docs/benchmarks/benchmarks.md) - formal definitions of ADE, FDE, latency, throughput, and memory usage, including formulas, units, and reporting conventions.

**Detection accuracy experiment:** [docs/detection_accuracy/detection_accuracy.md](docs/detection_accuracy/detection_accuracy.md) - standalone experiment characterising the accuracy of the YOLO + ZED depth stage independently of the Kalman filter, with setup, results and analysis.

**SVO2 format:** [docs/system_design/svo2_format.md](docs/system_design/svo2_format.md) - brief reference on the Stereolabs SVO2 recording format and what data it contains.
