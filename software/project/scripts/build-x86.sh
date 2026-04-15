#!/bin/bash
set -e
docker build -f docker/Dockerfile.x86 -t 3dpipe:x86 .
