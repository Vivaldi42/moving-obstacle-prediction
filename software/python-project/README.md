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

Build the x86 image:
```bash
docker build -f docker/Dockerfile.x86 -t 3dpipe-python:x86 .
```

Allow Docker to access your display:
```bash
xhost +local:docker
```

Run the default RGB stream prototype:
```bash
docker compose up python-prototype-x86
```

Run a different prototype:
```bash
PYTHON_COMMAND="python src/object_detection.py" docker compose up python-prototype-x86
```

## Jetson Orin Nano

Build the Jetson image on the Jetson:
```bash
docker build -f docker/Dockerfile.jetson -t 3dpipe-python:jetson .
```

Allow Docker to access your display:
```bash
xhost +local:docker
```

Run:
```bash
docker compose up python-prototype-jetson
```

## Prototype Scripts

- `src/rgb_live_stream.py`: left RGB camera stream
- `src/depth_map_live_stream.py`: depth visualization
- `src/rgb_d_live_stream.py`: RGB plus depth overlay
- `src/object_detection.py`: ZED object detection overlay
- `src/tennis_ball_3d_position.py`: HSV tennis-ball tracking with raw ZED depth XYZ output

## Notes

- Python dependencies live in `requirements.txt`.
- The Docker image installs the ZED Python API when `/usr/local/zed/get_python_api.py` is available.
- Keep this folder prototype-oriented; promote stable code to `../cpp-project` when you want it in the C++ app.
