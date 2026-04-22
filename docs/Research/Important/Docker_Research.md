# Docker Research

## Virtual Machine (VM)

A VM is a software emulation of a physical computer that runs on top of a host machine via a program called a **hypervisor** (e.g. VMware, VirtualBox, Hyper-V). Each VM includes a full guest OS, virtualized hardware (CPU, RAM, disk, network), and is completely isolated from other VMs on the same host. Because each VM carries its own OS kernel, VMs are heavy in terms of disk space and boot time. The hypervisor can either run directly on hardware (Type 1, "bare-metal") or on top of a host OS (Type 2). VMs provide strong isolation but at a significant resource overhead cost compared to containers.

![Docker vs VM](/images/docker_vs_VM.png)

## Docker

Docker is a platform for building, packaging, and running applications in containers. Unlike VMs, Docker containers share the host machine's OS kernel rather than running their own, making them significantly lighter and faster to start. Docker uses Linux kernel features - specifically namespaces (for isolation) and cgroups (for resource limiting) - to isolate containers from each other and from the host. An application and all its dependencies are packaged into a Docker image, which can then be run as a container on any machine that has Docker installed, regardless of the underlying system configuration. This solves the "works on my machine" problem by ensuring consistent environments across development, testing, and production. 

Using Docker it is possible to design a program that works only on a very new version of an OS using a host machine that has not been updated in years

## Docker Image

A Docker image is a read-only, layered package that contains everything needed to run an application - the code, runtime, libraries, environment variables, and configuration files. Images are built from a set of instructions defined in a Dockerfile, and each instruction creates a new read-only layer on top of the previous one. These layers are stacked and cached, meaning if only one layer changes, only that layer needs to be rebuilt or re-downloaded. Images are stored in a registry (e.g. Docker Hub) and can be pulled to any machine with Docker installed. When you run an image, Docker adds a thin writable layer on top and that running instance is called a container.

## Docker Container

A Docker container is a running instance of a Docker image. It is an isolated, lightweight process that runs on the host machine's OS kernel, with its own filesystem, network interface, and process space provided by Linux namespaces and cgroups. The container's filesystem is composed of the image's read-only layers plus a thin writable layer on top - any changes made inside the container (files written, packages installed) go into that writable layer and are lost when the container is removed unless explicitly persisted via **volumes**. Multiple containers can be run from the same image simultaneously, each fully isolated from the others. Containers start in milliseconds and consume far fewer resources than VMs because there is no guest OS overhead.
In containers everything runs as root.

## Dockerfile

A Dockerfile is a plain text file containing a sequential list of instructions that Docker uses to build an image. Each instruction (e.g. `FROM`, `RUN`, `COPY`, `CMD`) creates a new layer in the resulting image. `FROM` defines the base image to start from, `RUN` executes shell commands during the build process, `COPY` adds files from the host into the image, and `CMD` or `ENTRYPOINT` defines what command runs when a container starts. The Dockerfile is the single source of truth for how an image is constructed, making image builds reproducible and version-controllable. A typical workflow is: write Dockerfile -> run `docker build` -> get a Docker image -> run it as a container.

# References

https://www.netapp.com/blog/containers-vs-vms/

https://www.docker.com/