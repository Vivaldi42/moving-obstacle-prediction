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

## Current Status

- The x86 Docker flow is the main working development path.
- The Jetson Docker flow is still experimental on Jetson Orin Nano hosts running L4T 36.5.x.
- The reason is not a repo configuration gap alone: the latest matching ZED Docker image for Jetson L4T 36.5 is currently not published by the supplier, Stereolabs.
- Because of that, the Jetson Dockerfile currently uses the closest available published image, `stereolabs/zed:5.2-devel-l4t-r36.4`.
- This is still a host/container L4T mismatch on an L4T 36.5 system meaning that the system cannot be tested on Jetson hosts available to us.

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

!!! IMPORTANT: A correct base image needs to be used in Dockerfile.jetson. Check what is the image suitable for the Jetson platform you work with. !!!

## Notes

- `DISPLAY` and `/tmp/.X11-unix` are passed through so the OpenCV window can open.
- `privileged: true` is used to keep camera access simple during testing.
- x86 and Jetson use separate build folders to avoid cross-platform build cache issues.
- The Jetson base image should match the Jetson host L4T version.
- For Jetson hosts on L4T 36.5.x, a matching ZED Docker image is currently not available from Stereolabs.
- This repo currently tries `stereolabs/zed:5.2-devel-l4t-r36.4` as the closest published build-capable image for Jetson.
