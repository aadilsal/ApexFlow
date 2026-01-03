# Deployment & Environment Guide

ApexFlow is designed to be cloud-portable and reproducible.

## Environment Configuration

Configuration is managed via `config/retraining.yaml` and environment variables.

### Key Environment Variables
- `APEX_API_KEY`: Secret key for API access.
- `MLFLOW_TRACKING_URI`: Endpoint for the MLflow server.
- `ENVIRONMENT`: `development`, `staging`, or `production`.

## Local Development (Docker Compose)

The easiest way to run the full stack:
```bash
docker-compose up -d
```
This starts:
- **API**: `localhost:8000`
- **MLflow**: `localhost:5000`
- **Grafana**: `localhost:3000`
- **PostgreSQL**: Internal networking only.

## Production Deployment (Cloud Run)

The images are pushed to the registry using `./scripts/push_image.sh`. 
Deployment to Google Cloud Run uses `deploy/cloud-run.yaml`.

### Resource Requirements (Per Instance)
- **CPU**: 1.0 vCPU (Guaranteed)
- **Memory**: 2GB (To accommodate model loading and pandas processing)
- **Concurrency**: 80 concurrent requests per container.

## CI/CD Pipeline

Pushes to `main` trigger:
1. **CI**: Lints and unit tests.
2. **Build**: Multi-stage Docker build.
3. **Staging**: Deploy to the staging environment.
4. **Smoke Test**: Validate health and latency.
5. **Production**: Blue-green promotion upon manual or automated approval.
