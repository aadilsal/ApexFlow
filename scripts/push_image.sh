#!/bin/bash
# scripts/push_image.sh
# Packaging and publishing the prediction service to a container registry

set -e

REGISTRY=${1:-docker.io/apexflow}
SERVICE_NAME="lap-time-predictor"
GIT_SHA=$(git rev-parse --short HEAD)
MODEL_VERSION=${2:-"v1.0.0"}

FULL_IMAGE_NAME="$REGISTRY/$SERVICE_NAME"

echo "📦 Building image for $SERVICE_NAME..."
docker build -t "$FULL_IMAGE_NAME:$GIT_SHA" -t "$FULL_IMAGE_NAME:latest" -t "$FULL_IMAGE_NAME:$MODEL_VERSION" -f Dockerfile .

echo "🚀 Pushing image $FULL_IMAGE_NAME to registry..."
# docker push "$FULL_IMAGE_NAME:$GIT_SHA"
# docker push "$FULL_IMAGE_NAME:latest"
# docker push "$FULL_IMAGE_NAME:$MODEL_VERSION"

echo "✅ Image $FULL_IMAGE_NAME:$GIT_SHA successfully pushed!"
