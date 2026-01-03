# ApexFlow: F1 Lap-Time Prediction Platform

ApexFlow is a production-grade, end-to-end MLOps platform designed for real-time Formula 1 lap-time prediction. It leverages professional telemetry, automated retraining, and cloud-native orchestration to deliver race-weekend insights.

## 🏎️ Overview

This project implements a full ML lifecycle including:
- **Data Engineering**: DVC-tracked telemetry processing with schema validation.
- **Model Engineering**: XGBoost/LightGBM with Optuna hyperparameter tuning.
- **Automated Retraining**: Drift-triggered incremental learning via Prefect.
- **Inference Service**: Secure FastAPI service with uncertainty estimation.
- **Observability**: Prometheus/Grafana stack for performance & drift tracking.
- **Orchestration**: Dockerized blue-green deployments via GitHub Actions.

## 🛠️ Tech Stack

- **Core**: Python 3.10
- **Tracking**: MLflow (OSS)
- **Data**: DVC (OSS)
- **API**: FastAPI + Uvicorn
- **Monitor**: Prometheus + Grafana + Loki
- **Deploy**: Docker + Docker Compose + GHA

## 📁 Repository Structure

```text
.
├── .github/workflows/    # CI/CD pipelines
├── config/               # YAML environment configs
├── data/                 # Data samples (versioned by DVC)
├── deploy/               # Cloud Run/K8s manifests
├── docs/                 # Detailed documentation
├── monitoring/           # Prometheus/Grafana/Loki configs
├── scripts/              # Deployment and utility scripts
├── src/apex_flow/        # Core source code
│   ├── api/              # Prediction API layer
│   ├── data/             # Ingestion & validation
│   ├── modeling/         # Training & versioning
│   ├── monitoring/       # Drift & metrics logic
│   └── orchestration/    # Prefect retraining flows
└── tests/                # Unit, integration, & quality tests
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.10+

### Run the Cluster Locally
Launch the API, MLflow, and Monitoring stack in one command:
```bash
docker-compose up -d
```

### Get a Prediction
```bash
curl -X POST "http://localhost:8000/v1/predict" \
     -H "X-Apex-Key: race-weekend-key-2026" \
     -H "Content-Type: application/json" \
     -d '{
       "driver_id": "HAM",
       "circuit_id": "monaco",
       "fuel_load": 50.0,
       "tire_compound": "SOFT",
       "track_temp": 35.5,
       "session_type": "RACE"
     }'
```

## 📚 Documentation

For deep dives, troubleshooting, and contributing, see:
- [Architecture & Data Flow](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Troubleshooting Runbooks](docs/troubleshooting.md)
- [Data Dictionary](docs/data_dictionary.md)

---
*Built with ❤️ for F1 Engineers.*
