# 3dpipe Python Prototypes (Docker + ZED SDK)

This folder is the Python prototype companion to `../cpp-project`.

Use it for quick ZED, OpenCV, depth, and detection experiments. When a prototype
is worth keeping, port the useful parts to `../cpp-project`.

The Docker layout intentionally mirrors the C++ project:
- x86 (`linux/amd64`) uses `docker/Dockerfile.x86`
- Jetson Orin Nano (`linux/arm64`) uses `docker/Dockerfile.jetson`
- `docker-compose.yml` mounts this folder into `/app`
- GUI support is enabled through X11
- camera access is kept simple with `privileged: true`

## Current Status

- The x86 Docker flow is the main working development path.
- The Jetson Docker flow is still experimental on Jetson Orin Nano hosts running L4T 36.5.x.
- The Jetson Dockerfile currently uses `stereolabs/zed:5.2-devel-l4t-r36.4`, matching the current C++ project setup.
- Check the Jetson host L4T version before treating the Jetson image as final.

## x86

The commands below assume you run them from the repo root (`obstacle_prediction`).

The x86 container needs NVIDIA GPU access because the ZED SDK uses CUDA for SVO playback and depth retrieval.
The prototype currently uses the depth mode configured inside `src/prototype.py`, which defaults to `PERFORMANCE` to reduce GPU memory pressure during startup.

Build the x86 image:
```bash
docker build -f software/python-project/docker/Dockerfile.x86 -t 3dpipe-python:x86 software/python-project
```

Allow Docker to access your display:
```bash
xhost +local:docker
```

If you see `NO GPU COMPATIBLE` or CUDA out-of-memory errors when starting the container, check that:

- the NVIDIA Container Toolkit is installed and working
- Docker can see the GPU
- no other GPU-heavy process is exhausting VRAM
- you are using the compose file in this repo, which now requests `gpus: all`

Run the default RGB stream prototype:
```bash
docker compose -f software/python-project/docker-compose.yml up python-prototype-x86
```

Run a different prototype:
```bash
PYTHON_COMMAND="python src/object_detection.py" \
docker compose -f software/python-project/docker-compose.yml up python-prototype-x86
```

Run the YOLO tennis-ball tracker:
```bash
PYTHON_COMMAND="python src/tennis_ball_yolo.py" \
docker compose -f software/python-project/docker-compose.yml up python-prototype-x86
```

Run the SVO2 prototype against a host dataset directory:
```bash
xhost +local:docker
ZED_DATASET_DIR=/home/vladi/Documents/ZED/Dataset/Raw \
PYTHON_COMMAND="python src/prototype.py /datasets/HD720_SN39239193_13-45-06.svo2" \
docker compose -f software/python-project/docker-compose.yml up python-prototype-x86
```

Write outputs back into the repo from inside the container:
```bash
ZED_DATASET_DIR=/home/vladi/Documents/ZED/Dataset/Raw \
PYTHON_COMMAND="python src/prototype.py /datasets/HD720_SN39239193_13-45-06.svo2 --output-csv /app/output_detections.csv --output-video /app/output_video.mp4 --debug-dir /app/debug_frames" \
docker compose -f software/python-project/docker-compose.yml up python-prototype-x86
```

## Jetson Orin Nano

Build the Jetson image on the Jetson:
```bash
docker build -f software/python-project/docker/Dockerfile.jetson -t 3dpipe-python:jetson software/python-project
```

Allow Docker to access your display:
```bash
xhost +local:docker
```

Run:
```bash
docker compose -f software/python-project/docker-compose.yml up python-prototype-jetson
```

## Prototype Scripts

- `src/rgb_live_stream.py`: left RGB camera stream
- `src/depth_map_live_stream.py`: depth visualization
- `src/rgb_d_live_stream.py`: RGB plus depth overlay
- `src/object_detection.py`: ZED object detection overlay
- `src/tennis_ball_3d_position.py`: HSV tennis-ball tracking with raw ZED depth XYZ output
- `src/tennis_ball_yolo.py`: YOLO26 tennis-ball tracking with ZED depth, 3D XYZ, and Kalman prediction

## Notes

- Python dependencies live in `requirements.txt`.
- When overriding `PYTHON_COMMAND`, quote the full command string so Docker Compose receives it as one value.
- `ZED_DATASET_DIR` mounts a host folder into the container at `/datasets`.
- The Docker image installs the ZED Python API when `/usr/local/zed/get_python_api.py` is available.
- Keep this folder prototype-oriented; promote stable code to `../cpp-project` when you want it in the C++ app.
- If you prefer running commands from inside `software/python-project`, remove the `software/python-project/` prefixes from the Docker paths.


# Comands to run:

```
docker build -f docker/Dockerfile.x86 -t 3dpipe-python:x86 .
xhost +local:docker
ZED_DATASET_DIR=/home/vladi/Documents/ZED/Dataset/Raw \
PYTHON_COMMAND="python src/prototype.py /datasets/HD720_SN39239193_13-45-06.svo2 --output-csv /app/output_detections.csv --output-video /app/output_video.mp4 --debug-dir /app/debug_frames" \
docker compose up python-prototype-x86
```
