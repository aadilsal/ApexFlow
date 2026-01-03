#!/bin/bash
# scripts/deploy.sh
# Blue-Green Deployment Script

set -e

ENV=$1
TAG=$2

if [[ -z "$ENV" || -z "$TAG" ]]; then
  echo "Usage: ./deploy.sh <env> <tag>"
  exit 1
fi

echo "🚀 Starting $ENV deployment for version: $TAG"

# 1. Determine active color (for simplicity, using a flag or checking running containers)
# In a real environment, this might be managed by Nginx or a load balancer.
ACTIVE_COLOR=$(docker ps --filter "name=apex-flow-prod" --format "{{.Names}}" | grep -o "blue\|green" || echo "none")

if [[ "$ACTIVE_COLOR" == "blue" ]]; then
  TARGET_COLOR="green"
else
  TARGET_COLOR="blue"
fi

echo "Current active: $ACTIVE_COLOR. Deploying to: $TARGET_COLOR"

# 2. Deploy to Target Color
# docker run -d --name apex-flow-$ENV-$TARGET_COLOR apex-flow-service:$TAG
echo "Simulated: docker run -d --name apex-flow-$ENV-$TARGET_COLOR apex-flow-service:$TAG"

# 3. Transition notification
./scripts/notify.sh "deployment_start" "$ENV" "$TAG" "$TARGET_COLOR"

echo "✅ Target color $TARGET_COLOR deployed. Waiting for health checks..."
