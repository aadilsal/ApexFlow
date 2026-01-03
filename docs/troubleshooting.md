# Troubleshooting & Runbooks

Operational guide for debugging ApexFlow in production.

## 🔴 API Returning 500 or Not Responding

**Symptoms**: `curl` fails with timeout or internal server error.
**Probable Causes**: 
- Model not loaded on startup.
- Database connection pool exhausted.
- Instance OOM (Out of Memory).

**Resolution Steps**:
1. Check `/health` endpoint. If `model_loaded: false`, verify MLflow URI connectivity.
2. Inspect logs via Grafana Loki: `job="apexflow" | level="error"`.
3. Restart container: `docker-compose restart api`.

## 🟡 High Latency Alerts (P99 > 500ms)

**Symptoms**: Grafana shows latency spikes.
**Probable Causes**: 
- High request throughput during Qualifying peak.
- Heavy feature engineering on batch requests.

**Resolution Steps**:
1. Verify if auto-scaling is triggering. 
2. Check if a specific circuit or driver is causing the spike (check Prometheus labels).
3. Increase `MAX_BATCH_SIZE` or provision more CPU in `deploy/cloud-run.yaml`.

## 🟠 Drift Alerts Firing (Severity > 0.8)

**Symptoms**: Notifications in `logs/notifications.log` or webhook.
**Probable Causes**: 
- Sudden change in track temperature (rain/clouds).
- Major upgrade package on a car (Concept Drift).

**Resolution Steps**:
1. View the **Data Drift Dashboard** in Grafana to identify the shifting feature.
2. Manually trigger a retraining flow if the automated optimizer is in cooldown.
3. Validate the new "Candidate" model performance against the drift session.

## ⚪ CI/CD Pipeline Failure

**Symptoms**: GitHub Actions workflow turns red.
**Probable Causes**: 
- DVC remote credentials expired.
- Model validation gate failure (Regression detected).

**Resolution Steps**:
1. Inspect the "Validation Gate" logs in the GitHub Actions runner.
2. If regression is "Statistically Significant", the code change might have introduced data leakage or feature breakage. Revert or patch.
