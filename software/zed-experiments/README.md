# ZED Algo Sandbox (Docker)

This is a minimal ZED SDK sandbox for quick algorithm experiments inside Docker.
It is modeled after `/home/vladi/Desktop/zed-body-docker` but lives entirely in
`/home/vladi/Desktop/obstacle_prediction/software/zed-experiments`.

## What lives where

On the host:
- `Dockerfile`
- `CMakeLists.txt`
- `src/main.cpp`

Inside the container/image:
- ZED SDK
- CUDA
- OpenCV
- copied source at `/app`
- built app at `/app/build/zed_algo_sandbox`

The host only stores source files. The program is compiled in Docker during `docker build`.

## What the apps do

C++ app:
- Opens the ZED camera, grabs the left image and depth, and overlays the
  center depth value on the video.
- Replace `runAlgorithm(...)` in `src/main.cpp` with your own experiments.

Python app:
- Opens the ZED camera, grabs depth, and prints the center depth value in the terminal.
- Use `src/py_zed_sample.py` as a starting point for Python experiments.

Press `q` or `Esc` in the video window to quit.

## Build

From this folder:

```bash
docker build -t zed-algo-sandbox .
```

## Run

Allow Docker to use your X display:

```bash
xhost +local:docker
```

Run the C++ app:

```bash
docker run --rm -it \
  --gpus all \
  --privileged \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  zed-algo-sandbox
```

## Python (Manual Run)

Build the image as above, then:

```bash
docker run --rm -it \
  --gpus all \
  --privileged \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  zed-algo-sandbox \
  /opt/venv/bin/python /app/src/rgb_live_stream.py
```

## Python Sandbox (No ZED API)

If you just want a quick Python entrypoint without touching ZED:

```bash
docker run --rm -it \
  --gpus all \
  --privileged \
  -e DISPLAY=$DISPLAY \
  -e QT_X11_NO_MITSHM=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  zed-algo-sandbox \
  /opt/venv/bin/python /app/src/py_sandbox.py
```
Description:
docker run --rm -it \
Starts a container interactively with a TTY, and removes it when it exits.

--gpus all
Exposes all host GPUs to the container (NVIDIA runtime).

--privileged
Gives the container extended permissions (access to devices, etc.).

-e DISPLAY=$DISPLAY
Passes your host X11 display so GUI windows can open.

-e QT_X11_NO_MITSHM=1
Disables MIT-SHM for Qt, which avoids shared-memory issues in Docker + X11.

-v /tmp/.X11-unix:/tmp/.X11-unix:rw
Mounts the X11 socket so the container can talk to your X server.

zed-algo-sandbox
The Docker image name.

/opt/venv/bin/python /app/src/live_stream.py
Runs the Python interpreter from a virtualenv inside the container, executing your live_stream.py script.

## Notes

- `--gpus all` gives the container CUDA access.
- `--privileged` is the simplest way to pass the ZED device into the container.
- If the build fails on `cuda.h`, make sure `CMakeLists.txt` includes `${CUDA_INCLUDE_DIRS}`.
- If the window does not open, the usual problem is X11/Wayland display forwarding, not the app build.
