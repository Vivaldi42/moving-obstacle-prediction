# 3dpipe (Docker + ZED SDK)

This repo is a starter scaffold to build and run `3dpipe` inside Docker on:
- x86 (`linux/amd64`)
- Jetson (`linux/arm64`)

We’re using official Stereolabs ZED SDK images as the base.

## Quick Start (x86 Dev Mode)

Build the dev environment image:
```bash
./scripts/build-x86.sh
```

Allow Docker to access your X display (GUI):
```bash
xhost +local:docker
```

Run:
```bash
docker compose up 3dpipe-x86
```

In dev mode, the repo is mounted into `/app` inside the container, so your local
source files are used directly. The Dockerfiles do not copy your project code.
On each `docker compose up 3dpipe-x86`, the container:
- configures CMake
- rebuilds the app
- runs `./build/3dpipe`

This is convenient while actively changing code because you do not need to
rebuild the whole Docker image after every source edit.

## Production Style (x86)

If you want a self-contained image that does not depend on a source-code mount:

Build:
```bash
./scripts/build-x86-prod.sh
```

Run:
```bash
xhost +local:docker
docker compose --profile prod up 3dpipe-prod
```

In this mode, the image copies the source code during `docker build`, compiles
it into the image, and then runs without mounting your repo into `/app`.

## Jetson Dev Mode

Build the Jetson dev environment image on the Orin Nano:
```bash
docker build -f docker/Dockerfile.jetson -t 3dpipe:jetson .
```

Run on the Orin Nano:
```bash
xhost +local:docker
docker compose up 3dpipe-jetson
```

## Jetson Note

Your Jetson reported `R36 (rev 5.0)` which corresponds to **L4T 36.5.0** and
maps to **JetPack 6.2.2**. citeturn1search3turn1search0

We are choosing to **downgrade to JetPack 6.1 / 6.2.1 (L4T 36.4.x)** so we can
use the existing Jetson ZED Docker tags.

`docker/Dockerfile.jetson` and `docker/Dockerfile.jetson.prod` use:
`stereolabs/zed:5.2-tools-devel-l4t-r36.4`

If you later upgrade back to L4T 36.5.x, we must switch to a matching
`l4t-r36.5` tag once Stereolabs publishes it.

## Runtime Flags Explained

The compose file enables GPU, camera, and GUI access:
- NVIDIA GPU reservation gives CUDA/GPU access
- `privileged: true` is the simplest way to expose the ZED camera devices
- `DISPLAY` and `/tmp/.X11-unix` enable X11 GUI
- `QT_X11_NO_MITSHM=1` avoids a common Qt/X11 shared-memory issue in Docker

## Dev Mode Mount

This line in `docker-compose.yml`:

```yaml
- .:/app:rw
```

means:
- `.` = your current project folder on the host
- `/app` = where that folder appears inside the container
- `rw` = the container can read and write those files

So the container sees your live working tree from VS Code and builds from that
mounted source tree.

## Dev Vs Prod

Use dev mode when:
- you are actively editing code in VS Code
- you want fast iteration without rebuilding the whole image

Steps:
1. Build the environment image when needed: `./scripts/build-x86.sh`. Run it when: 
  - the Dockerfile is changed
  - Ubuntu packages are added
  - or system-level dependencies are chagned
2. Develop normally in VS Code.
3. Run the project: `docker compose up 3dpipe-x86`
4. Docker mounts your code, compiles it, and runs it.

Use production style when:
- you want a portable image
- you do not want to depend on host source mounts at runtime
- you are closer to deployment
