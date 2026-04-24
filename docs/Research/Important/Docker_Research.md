# Docker Research

## Research Question: How can Docker be used to develop a portable pipeline?

This document describes the major Docker concepts related to the project. It was developed during the time I experimented with Docker and setting up a portable environment and gives an overview of the technology and its application.

---

## 1. Background - Virtualization Concepts

### Virtual Machine (VM)

A VM is a software emulation of a physical computer that runs on top of a host machine via a program called a **hypervisor** (e.g. VMware, VirtualBox, Hyper-V). Each VM includes a full guest OS, virtualized hardware (CPU, RAM, disk, network), and is completely isolated from other VMs on the same host. Because each VM carries its own OS kernel, VMs are heavy in terms of disk space and boot time. The hypervisor can either run directly on hardware (Type 1, "bare-metal") or on top of a host OS (Type 2). VMs provide strong isolation but at a significant resource overhead cost compared to containers.

### Docker

Docker is a platform for building, packaging, and running applications in containers. Unlike VMs, Docker containers share the host machine's OS kernel rather than running their own, making them significantly lighter and faster to start. Docker uses Linux kernel features - specifically namespaces (for isolation) and cgroups (for resource limiting) - to isolate containers from each other and from the host. An application and all its dependencies are packaged into a Docker image, which can then be run as a container on any machine that has Docker installed, regardless of the underlying system configuration. This solves the "works on my machine" problem by ensuring consistent environments across development, testing, and production. Using Docker it is possible to design a program that works only on a very new version of an OS using a host machine that has not been updated in years.


![Docker vs VM](/images/docker_vs_VM.png)

---

## 2. Core Docker Concepts

### Docker Image

A Docker image is a read-only, layered package that contains everything needed to run an application - the code, runtime, libraries, environment variables, and configuration files. Images are built from a set of instructions defined in a Dockerfile, and each instruction creates a new read-only layer on top of the previous one. These layers are stacked and cached, meaning if only one layer changes, only that layer needs to be rebuilt or re-downloaded. Images are stored in a registry (e.g. Docker Hub) and can be pulled to any machine with Docker installed. When an image is run, Docker adds a thin writable layer on top and that running instance is called a container.

### Docker Container

A Docker container is a running instance of a Docker image. It is an isolated, lightweight process that runs on the host machine's OS kernel, with its own filesystem, network interface, and process space provided by Linux namespaces and cgroups. The container's filesystem is composed of the image's read-only layers plus a thin writable layer on top - any changes made inside the container (files written, packages installed) go into that writable layer and are lost when the container is removed unless explicitly persisted via mounts. Multiple containers can be run from the same image simultaneously, each fully isolated from the others. Containers start in milliseconds and consume far fewer resources than VMs because there is no guest OS overhead. By default containers run as root, but this can be changed via the `USER` instruction in the Dockerfile or the `--user` flag at runtime.

### Dockerfile

A Dockerfile is a plain text file containing a sequential list of instructions that Docker uses to build an image. Each instruction (e.g. `FROM`, `RUN`, `COPY`, `CMD`) creates a new layer in the resulting image. `FROM` defines the base image to start from, `RUN` executes shell commands during the build process, `COPY` adds files from the host into the image, and `CMD` or `ENTRYPOINT` defines what command runs when a container starts. The Dockerfile is the single source of truth for how an image is constructed, making image builds reproducible and version-controllable. A typical workflow is: write Dockerfile -> run `docker build` -> get a Docker image -> run it as a container.

#### ENTRYPOINT vs CMD

Both `ENTRYPOINT` and `CMD` define what runs when a container starts, but they behave differently. `ENTRYPOINT` sets the fixed executable that always runs - it cannot be overridden by arguments passed to `docker run`. `CMD` sets default arguments that can be overridden at runtime. When both are used together, `ENTRYPOINT` is the executable and `CMD` provides its default arguments. For example, `ENTRYPOINT ["python"]` and `CMD ["app.py"]` runs `python app.py` by default, but `docker run myimage script.py` would run `python script.py` instead.

### Base Image

A base image is the starting point of a Dockerfile, specified by the 
`FROM` instruction. It provides the initial filesystem and environment 
that all subsequent instructions build upon. Base images range from 
minimal (e.g. `scratch`, which is completely empty, or `alpine`, a ~5MB 
Linux distribution) to full OS images (e.g. `ubuntu:22.04`) to 
language-specific images (e.g. `python:3.11-slim`). Choosing the right 
base image directly affects the final image size, security surface area,
 and **architecture compatibility**. Official images on Docker Hub 
typically provide variants for multiple architectures under the same 
tag.

---

## 3. Docker Infrastructure

### Docker Registry / Docker Hub

A Docker registry is a storage and distribution server for Docker images. When you run `docker push` or `docker pull`, you are interacting with a registry. **Docker Hub** is the default public registry maintained by Docker Inc., where most official base images (e.g. `ubuntu`, `python`, `node`) are hosted. Private registries also exist - either self-hosted or cloud-provided (e.g. AWS ECR, GitHub Container Registry) - for storing proprietary images. Images in a registry are identified by a name and tag, e.g. `python:3.11-slim`, where `python` is the repository and `3.11-slim` is the tag.

### Docker Network

A Docker network is a virtual network that allows containers to communicate with each other and with the outside world. By default, Docker creates a `bridge` network on the host, and containers on the same bridge network can reach each other by container name. Docker supports several network drivers: `bridge` (default, single host), `host` (container shares the host's network stack), and `overlay` (multi-host, used in orchestration). Isolating containers in separate networks is a common security practice, ensuring containers can only communicate with other containers they are explicitly connected to.

### Docker Mounts (Volumes, Bind Mounts, tmpfs)

Docker provides three mechanisms for mounting data into a container. **Named volumes** are managed by Docker, stored at `/var/lib/docker/volumes/`, and are the recommended way to persist data across container restarts and removals. **Bind mounts** map a specific path on the host filesystem directly into the container, giving the container access to host files - commonly used in development to mount source code. **tmpfs mounts** store data in the host's memory only, never written to disk, useful for sensitive or temporary data. All three are specified under the `volumes:` key in a Compose file, which is a source of naming confusion - "volumes" in Compose syntax refers to all mount types, not exclusively Docker-managed named volumes.

---

## 4. Multi-container Configuration

### Docker Compose

Docker Compose is a tool for defining and running multi-container Docker applications using a single YAML file (`docker-compose.yml`). In this file all services (containers) are declared, their images or build context, environment variables, volumes, networks, and port mappings. Running `docker compose up` builds and starts all defined services together. It is primarily used for local development and testing of multi-container setups (e.g. an app container + a database container). Compose does not handle production-scale orchestration - that is the domain of tools like Kubernetes.

---

## 5. Cross-platform

### Multi-stage Build

A multi-stage build is a Dockerfile technique where multiple `FROM` instructions are used in sequence, each starting a new build stage. Earlier stages are used to compile or build the application, and only the necessary output artifacts are copied into a final, minimal stage. This avoids shipping build tools, compilers, and intermediate files in the final image, significantly reducing image size and attack surface. For example: stage 1 uses a full `gcc` image to compile a binary, stage 2 copies only that binary into a minimal `alpine` image. Each stage can use a different base image.

### Multi-platform Build / `docker buildx`

`docker buildx` is an extended Docker CLI plugin for building images with advanced features, most importantly **multi-platform builds**. A multi-platform build produces a single image that contains variants for multiple architectures (e.g. `linux/amd64`, `linux/arm64`, `linux/arm/v7`) bundled together in a **manifest list**. When a user pulls the image, Docker automatically selects the correct variant for their architecture. `buildx` uses either native hardware, cross-compilation, or QEMU emulation to build each architecture variant. It requires a builder instance created with `docker buildx create` and images are typically pushed directly to a registry rather than loaded locally.

### Platform Flag (`--platform`)

The `--platform` flag is used in both `docker build` and `FROM` instructions to explicitly specify the target architecture for a build or image pull. For example, `docker build --platform linux/arm64` builds the image for ARM64 regardless of the host machine's architecture. In a Dockerfile, `FROM --platform=linux/amd64 python:3.11` forces that specific base image variant to be used. In multi-platform builds with `buildx`, `--platform` accepts a comma-separated list (e.g. `--platform linux/amd64,linux/arm64`) to build all variants in one command. This flag is the primary mechanism for controlling architecture targeting throughout the build pipeline.

### QEMU / Emulation

QEMU is an open-source hardware emulator that allows software compiled for one CPU architecture to run on a different one. In the Docker context, QEMU is used by `buildx` to build images for architectures that differ from the host - for example, building an ARM64 image on an x86 machine. Docker Desktop includes QEMU support by default; on Linux it requires registering QEMU binary formats with the kernel via `binfmt_misc` (typically done by running the `tonistiigi/binfmt` image). Emulation is slower than native builds - sometimes significantly - so for performance-critical pipelines, building on native hardware or using cross-compilation is preferred over QEMU emulation.

---

## 6. Conclusion

Docker enables portable pipelines by packaging applications and their dependencies into images that run consistently across different machines and environments. The combination of multi-platform builds (`docker buildx`), the `--platform` flag, and QEMU emulation allows a single image to target multiple CPU architectures (x86, ARM, and others) from a single build command. Base image selection, multi-stage builds, and proper use of mounts and networks further allow the pipeline to be efficient, minimal, and adaptable across both development and production environments.

---

## 7. References

- Docker official documentation: https://docs.docker.com
- Docker buildx documentation: https://docs.docker.com/buildx/working-with-buildx/
- Multi-platform builds: https://docs.docker.com/build/building/multi-platform/
- QEMU / binfmt setup: https://github.com/tonistiigi/binfmt
-  Containers vs. Virtual Machines (VMs): https://www.netapp.com/blog/containers-vs-vms/
