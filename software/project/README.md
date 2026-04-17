# 3dpipe (Docker + ZED SDK)

This repo keeps a simple Docker setup for running `3dpipe` on:
- x86 (`linux/amd64`)
- Jetson Orin Nano (`linux/arm64`)

We use one Docker image definition per platform:
- `docker/Dockerfile.x86`
- `docker/Dockerfile.jetson`

Both services mount the repo into `/app`, build the project with CMake inside the
container, and run the app with GUI support enabled through X11. There is no
custom entrypoint script.

## x86

Build the x86 image:
```bash
docker build -f docker/Dockerfile.x86 -t 3dpipe:x86 .
```

Allow Docker to access your display:
```bash
xhost +local:docker
```

Run:
```bash
docker compose up 3dpipe-x86
```

The x86 container builds into `build-x86/`.

## Jetson Orin Nano

Build the Jetson image on the Jetson:
```bash
docker build -f docker/Dockerfile.jetson -t 3dpipe:jetson .
```

Allow Docker to access your display:
```bash
xhost +local:docker
```

Run:
```bash
docker compose up 3dpipe-jetson
```

The Jetson container builds into `build-jetson/`.

## Notes

- `DISPLAY` and `/tmp/.X11-unix` are passed through so the OpenCV window can open.
- `privileged: true` is used to keep camera access simple during testing.
- x86 and Jetson use separate build folders to avoid cross-platform build cache issues.
- The Jetson base image must match the Jetson host L4T version. This repo currently tries `stereolabs/zed:5.2-devel-l4t-r36.4`, which is the closest published build-capable image we found, but it is still a mismatch if the host is on L4T 36.5.
