#!/bin/bash
# scripts/rollback.sh
# Automated Rollback Script

ENV=$1
REASON=$2

if [[ -z "$ENV" ]]; then
  echo "Usage: ./rollback.sh <env> <reason>"
  exit 1
fi

echo "⚠️ ROLLING BACK $ENV environment due to: $REASON"

# 1. Revert traffic to previously active color
# In blue-green, this just means switching the load balancer back
echo "Simulated: Reverting traffic to previous stable version"

# 2. Kill the failed target color
# docker rm -f apex-flow-$ENV-failed-target
echo "Simulated: Removing failed deployment"

# 3. Notification
./scripts/notify.sh "rollback_triggered" "$ENV" "previous_stable" "$REASON"

echo "✅ Rollback completed for $ENV"
