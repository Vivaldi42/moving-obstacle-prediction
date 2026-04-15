#!/bin/bash
set -e
docker build -f docker/Dockerfile.x86.prod -t 3dpipe:x86-prod .
