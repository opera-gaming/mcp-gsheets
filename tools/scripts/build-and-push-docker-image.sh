#!/usr/bin/env bash

set -e

IMAGE_TAG="${1}"

aws ecr get-login-password | docker login --username AWS --password-stdin "${DOCKER_REGISTRY}"

#  Build and push the image.
docker build \
    --file Dockerfile \
    --tag "${DOCKER_REPOSITORY}:${IMAGE_TAG}" \
    --push .
