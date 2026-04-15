#!/bin/bash
set -e
docker build -f docker/Dockerfile.jetson.prod -t 3dpipe:jetson-prod .
